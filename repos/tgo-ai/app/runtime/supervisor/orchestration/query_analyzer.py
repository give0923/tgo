"""
LLM-powered query analysis implementation.

This module provides the concrete implementation for analyzing user queries,
decomposing them into sub-questions, and assigning them to appropriate agents.
"""

import json
import time
from typing import Dict, List, Optional

from app.core.logging import get_logger
from app.models.internal import CoordinationContext, AgentExecutionRequest
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from app.runtime.supervisor.infrastructure.services import AgentServiceClient

from ..interfaces.query_analyzer import IQueryAnalyzer
from ..models.coordination import QueryAnalysisResult, SubQuestion, ExecutionPlan, WorkflowType
from ..configuration.settings import QueryAnalysisConfig
from ..exceptions.coordination import QueryAnalysisError, ValidationError, LLMResponseError
from ..utils.validation import validate_query_analysis_result
from ..utils.prompts import format_agent_profiles, clean_json_response
from ..agents.system_agents import get_system_agent_by_type
from ..streaming.workflow_events import WorkflowEventEmitter


class LLMQueryAnalyzer(IQueryAnalyzer):
    """
    LLM-powered query analyzer that decomposes user queries and assigns agents.
    
    This implementation uses advanced LLM techniques to:
    - Understand user intent and complexity
    - Decompose multi-intent queries into focused sub-questions
    - Select optimal agents based on capabilities and context
    - Determine the best workflow execution pattern
    - Create detailed execution plans with dependencies
    """
    
    def __init__(
        self,
        agent_service_client: "AgentServiceClient",
        config: QueryAnalysisConfig
    ) -> None:
        self.agent_service = agent_service_client
        self.config = config
        self.logger = get_logger(__name__).bind(component="query_analyzer")

        # Create system agent for query analysis
        self.query_analysis_agent = get_system_agent_by_type("query_analysis")
    
    async def analyze_query(
        self,
        context: CoordinationContext,
        auth_headers: Dict[str, str],
        workflow_events: Optional[WorkflowEventEmitter] = None
    ) -> QueryAnalysisResult:
        """
        Analyze user query using LLM and create comprehensive coordination plan.
        
        This method implements the core logic flow:
        1. Build analysis prompt with context and agent information
        2. Call LLM with structured prompt for JSON response
        3. Parse and validate LLM response
        4. Create QueryAnalysisResult with exact format specified
        """
        start_time = time.time()
        
        self.logger.info(
            "Starting query analysis",
            user_message_length=len(context.message),
            team_id=context.team.id,
            available_agents=len(context.team.agents),
            max_agents=context.max_agents
        )

        try:
            # Build analysis prompt with context
            prompt = await self._build_analysis_prompt(context)

            # Emit query analysis started event
            if workflow_events:
                workflow_events.emit_query_analysis_started(
                    "Query Analysis Agent",
                    len(prompt)
                )

            # Execute query analysis agent
            agent_response = await self._execute_query_analysis_agent(
                context,
                prompt,
                auth_headers,
                enable_memory=False,
                session_id=context.session_id,
                user_id=context.user_id,
            )

            # Parse and validate response
            analysis_result = await self._parse_agent_response(agent_response, context)
            
            # Final validation
            await self.validate_analysis_result(analysis_result, context)
            
            analysis_time = time.time() - start_time

            # Emit query analysis completed event
            if workflow_events:
                workflow_events.emit_query_analysis_completed(analysis_result, analysis_time)

            self.logger.info(
                "Query analysis completed successfully",
                analysis_time=analysis_time,
                selected_agents=len(analysis_result.selected_agent_ids),
                workflow_pattern=analysis_result.workflow,
                is_complex=analysis_result.is_complex,
                confidence_score=analysis_result.confidence_score,
                sub_questions_count=len(analysis_result.sub_questions)
            )

            return analysis_result
            
        except Exception as e:
            analysis_time = time.time() - start_time

            # Emit query analysis failed event
            if workflow_events:
                workflow_events.emit_query_analysis_failed(str(e), "Query Analysis Agent")

            self.logger.error(
                "Query analysis failed",
                error=str(e),
                error_type=type(e).__name__,
                analysis_time=analysis_time
            )

            if isinstance(e, (QueryAnalysisError, ValidationError)):
                raise
            else:
                raise QueryAnalysisError(
                    f"Query analysis failed: {str(e)}",
                    user_query=context.message,
                    model_name=self.config.model_name,
                    cause=e
                ) from e
    
    async def validate_analysis_result(
        self,
        result: QueryAnalysisResult,
        context: CoordinationContext
    ) -> bool:
        """Validate analysis result for consistency and feasibility."""
        try:
            # Use utility function for comprehensive validation
            validation_errors = validate_query_analysis_result(result, context)
            
            if validation_errors:
                raise ValidationError(
                    f"Analysis result validation failed: {'; '.join(validation_errors)}",
                    validation_errors=validation_errors
                )
            
            self.logger.debug(
                "Analysis result validation passed",
                selected_agents=len(result.selected_agent_ids),
                workflow=result.workflow,
                confidence=result.confidence_score
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Analysis result validation failed",
                error=str(e),
                selected_agents=len(result.selected_agent_ids) if result.selected_agent_ids else 0
            )
            raise
    
    def get_supported_workflow_patterns(self) -> List[str]:
        """Get list of supported workflow patterns."""
        return [pattern.value for pattern in WorkflowType]
    
    async def _build_analysis_prompt(self, context: CoordinationContext) -> str:
        """Build comprehensive analysis prompt with context."""
        try:
            agent_profiles = format_agent_profiles(context.team.agents)

            prompt = f"""USER MESSAGE:
"{context.message}"

TEAM CONTEXT:
Team Name: {context.team.name}
Team Description: {context.team.instruction or "General purpose team"}
Session ID: {context.session_id or "default"}

COORDINATION REQUIREMENTS:
Maximum Agents: {context.max_agents}
Require Consensus: {context.require_consensus}
Timeout: {context.timeout} seconds

AVAILABLE AGENTS:
{agent_profiles}

Please analyze this query and provide a coordination plan in the required JSON format."""

            return prompt
        except Exception as e:
            raise QueryAnalysisError(
                f"Failed to build analysis prompt: {str(e)}",
                user_query=context.message,
                cause=e
            ) from e
    
    async def _execute_query_analysis_agent(
        self,
        context: CoordinationContext,
        prompt: str,
        auth_headers: Dict[str, str],
        enable_memory: bool,
        session_id: Optional[str],
        user_id: Optional[str],
    ) -> str:
        """Execute query analysis agent for coordination planning."""
        try:
            # Create agent execution request
            request = AgentExecutionRequest(
                message=prompt,
                config={},
                session_id=session_id or f"query_analysis_{int(time.time())}",
                user_id=user_id,
                enable_memory=enable_memory,
            )

            # Resolve provider credentials from team context
            creds = getattr(context.team, "llm_provider_credentials", None)
            if not creds:
                raise QueryAnalysisError(
                    "No LLM provider configured for team; set team.llm_provider_id or agent.llm_provider_id",
                    team_id=context.team.id,
                )
            agent_to_execute = self.query_analysis_agent.model_copy()
            # Ensure system agent uses team's model (no model in global config)
            agent_to_execute.model = context.team.model
            setattr(agent_to_execute, "llm_provider_credentials", creds)

            # Execute the query analysis agent
            print("prompt---->", prompt)
            response = await self.agent_service.execute_agent(
                agent=agent_to_execute,
                request=request,
                auth_headers=auth_headers
            )

            if not response.success:
                raise LLMResponseError(
                    f"Query analysis agent failed: {response.error}",
                    raw_response=response.content,
                    expected_format="JSON with coordination plan"
                )

            if not response.content or not response.content.strip():
                raise LLMResponseError(
                    "Query analysis agent returned empty response",
                    raw_response=response.content,
                    expected_format="JSON with coordination plan"
                )

            return response.content.strip()

        except Exception as e:
            import traceback
            self.logger.error(
                "Query analysis agent execution failed",
                error=str(e),
                agent_name=self.query_analysis_agent.name,
                prompt_length=len(prompt),
                traceback=traceback.format_exc()
            )
            # Print detailed error for debugging
            print(f"ERROR: Query analysis agent execution failed: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")

            if isinstance(e, LLMResponseError):
                raise
            else:
                raise QueryAnalysisError(
                    f"Query analysis agent execution failed: {str(e)}",
                    model_name=self.query_analysis_agent.model,
                    prompt_length=len(prompt),
                    cause=e
                ) from e
    
    async def _parse_agent_response(
        self,
        response: str,
        context: CoordinationContext
    ) -> QueryAnalysisResult:
        """Parse agent response into QueryAnalysisResult."""
        try:
            # Parse JSON response
            print("response---->",response)

            # Clean response - remove markdown code blocks if present
            cleaned_response = clean_json_response(response)

            data = json.loads(cleaned_response)
            
            # Extract and validate sub-questions
            sub_questions = []
            if "sub_questions" in data and data["sub_questions"]:
                for sq_data in data["sub_questions"]:
                    sub_question = SubQuestion(
                        id=sq_data["id"],
                        question=sq_data["question"],
                        assigned_agent_id=sq_data["assigned_agent_id"]
                    )
                    sub_questions.append(sub_question)
            
            # Extract and validate execution plan
            execution_plan = ExecutionPlan()
            if "execution_plan" in data and data["execution_plan"]:
                plan_data = data["execution_plan"]
                execution_plan = ExecutionPlan(
                    dependencies=plan_data.get("dependencies", []),
                    parallel_groups=plan_data.get("parallel_groups", []),
                    estimated_time=plan_data.get("estimated_time", 30.0)
                )
            
            # Create analysis result
            result = QueryAnalysisResult(
                selected_agent_ids=data["selected_agent_ids"],
                selection_reasoning=data["selection_reasoning"],
                workflow=data["workflow"],
                workflow_reasoning=data["workflow_reasoning"],
                confidence_score=data["confidence_score"],
                is_complex=data["is_complex"],
                sub_questions=sub_questions,
                execution_plan=execution_plan
            )
            
            return result
            
        except json.JSONDecodeError as e:
            raise LLMResponseError(
                f"Failed to parse LLM response as JSON: {str(e)}",
                raw_response=response,
                expected_format="Valid JSON object",
                parsing_errors=[str(e)]
            ) from e
        
        except KeyError as e:
            raise LLMResponseError(
                f"Missing required field in LLM response: {str(e)}",
                raw_response=response,
                expected_format="JSON with all required fields",
                parsing_errors=[f"Missing field: {str(e)}"]
            ) from e
        
        except Exception as e:
            raise LLMResponseError(
                f"Failed to parse LLM response: {str(e)}",
                raw_response=response,
                parsing_errors=[str(e)],
                cause=e
            ) from e
