"""
LLM-powered result consolidation implementation.

This module provides the concrete implementation for consolidating multiple
agent execution results into unified, coherent responses.
"""

import json
import time
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from app.core.logging import get_logger
from app.models.internal import CoordinationContext, AgentExecutionRequest

if TYPE_CHECKING:  # pragma: no cover
    from app.runtime.supervisor.infrastructure.services import AgentServiceClient

from ..interfaces.result_consolidator import IResultConsolidator
from ..streaming.workflow_events import WorkflowEventEmitter
from ..models.execution import ExecutionResult
from ..models.results import (
    ConsolidationResult, ConsolidationStrategy, ConsolidationRequest,
    ConflictResolution
)
from ..configuration.settings import ConsolidationConfig
from ..exceptions.coordination import ConsolidationError, LLMResponseError, ValidationError
from ..utils.prompts import format_execution_results, clean_json_response
from ..utils.logging import get_coordination_logger
from ..utils.metrics import MetricsCollector
from ..agents.system_agents import (
    get_system_agent_by_type,
    get_result_consolidation_instruction,
)
from ..streaming.workflow_events import WorkflowEventEmitter


class LLMResultConsolidator(IResultConsolidator):
    """
    LLM-powered result consolidator for intelligent response synthesis.

    This implementation:
    - Uses advanced LLM techniques to consolidate multiple responses
    - Detects and resolves conflicts between agent outputs
    - Builds consensus from diverse perspectives
    - Maintains source attribution and confidence scoring
    - Provides comprehensive conflict resolution
    """

    def __init__(
        self,
        agent_service_client: "AgentServiceClient",
        config: ConsolidationConfig
    ) -> None:
        self.agent_service = agent_service_client
        self.config = config
        self.logger = get_coordination_logger("result_consolidator")

        # Create system agent for result consolidation
        self.consolidation_agent = get_system_agent_by_type("result_consolidation")

    async def consolidate_results(
        self,
        execution_results: List[ExecutionResult],
        context: CoordinationContext,
        strategy: Optional[ConsolidationStrategy] = None,
        workflow_events: Optional[WorkflowEventEmitter] = None
    ) -> ConsolidationResult:
        """Consolidate multiple execution results into unified response."""
        with MetricsCollector("result_consolidation") as metrics:
            start_time = time.time()

            self.logger.info(
                "Starting result consolidation",
                total_results=len(execution_results),
                successful_results=sum(1 for r in execution_results if r.success),
                user_message_length=len(context.message)
            )

            # Emit consolidation started event
            if workflow_events:
                workflow_events.emit_consolidation_started(
                    str(self.consolidation_agent.id),
                    self.consolidation_agent.name,
                    len(execution_results)
                )

            try:
                # Filter successful results
                successful_results = [r for r in execution_results if r.success]

                if not successful_results:
                    raise ConsolidationError(
                        "No successful execution results to consolidate",
                        result_count=len(execution_results)
                    )

                # Emit initial progress
                if workflow_events:
                    workflow_events.emit_consolidation_progress(
                        current_step="Filtering and validating results",
                        progress_percentage=10.0,
                        total_results=len(execution_results),
                        processed_results=0
                    )

                # Select consolidation strategy if not provided
                if strategy is None:
                    strategy = self.select_consolidation_strategy(execution_results, context)

                # Emit strategy selection progress
                if workflow_events:
                    workflow_events.emit_consolidation_progress(
                        current_step=f"Strategy selected: {strategy.value}",
                        progress_percentage=25.0,
                        total_results=len(execution_results),
                        processed_results=0,
                        consolidation_strategy=strategy.value
                    )

                # Create consolidation request
                consolidation_request = ConsolidationRequest(
                    user_message=context.message,
                    execution_results=[self._result_to_dict(r) for r in successful_results],
                    consolidation_strategy=strategy,
                    require_consensus=context.require_consensus,
                    confidence_threshold=self.config.confidence_threshold,
                    max_response_length=self.config.max_response_length,
                    enable_memory=context.enable_memory,
                    session_id=context.session_id,
                    user_id=context.user_id,
                )

                # Emit request preparation progress
                if workflow_events:
                    workflow_events.emit_consolidation_progress(
                        current_step="Preparing consolidation request",
                        progress_percentage=40.0,
                        total_results=len(execution_results),
                        processed_results=len(successful_results),
                        consolidation_strategy=strategy.value
                    )

                # Perform consolidation using LLM synthesis
                # Emit synthesis progress
                if workflow_events:
                    workflow_events.emit_consolidation_progress(
                        current_step="Synthesizing responses with LLM",
                        progress_percentage=60.0,
                        total_results=len(execution_results),
                        processed_results=len(successful_results),
                        consolidation_strategy=strategy.value
                    )
                result = await self.synthesize_responses(consolidation_request, context, workflow_events)

                # Calculate final confidence score
                result.confidence_score = self.calculate_confidence_score(execution_results, result)

                # Emit final progress before completion
                if workflow_events:
                    workflow_events.emit_consolidation_progress(
                        current_step="Finalizing consolidation result",
                        progress_percentage=95.0,
                        total_results=len(execution_results),
                        processed_results=len(successful_results),
                        consolidation_strategy=strategy.value,
                        conflicts_detected=len([r for r in result.conflicts_resolved]),
                        conflicts_resolved=len(result.conflicts_resolved)
                    )

                consolidation_time = time.time() - start_time
                result.consolidation_time = consolidation_time

                metrics.add_metadata("strategy_used", strategy.value)
                metrics.add_metadata("conflicts_resolved", len(result.conflicts_resolved))
                metrics.add_metadata("confidence_score", result.confidence_score)

                # Emit consolidation completed event
                if workflow_events:
                    workflow_events.emit_consolidation_completed(result, str(self.consolidation_agent.id))

                self.logger.info(
                    "Result consolidation completed",
                    consolidation_time=consolidation_time,
                    strategy_used=strategy.value,
                    confidence_score=result.confidence_score,
                    conflicts_resolved=len(result.conflicts_resolved),
                    sources_used=len(result.sources_used)
                )

                return result

            except Exception as e:
                consolidation_time = time.time() - start_time

                self.logger.error(
                    "Result consolidation failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    consolidation_time=consolidation_time,
                    result_count=len(execution_results)
                )

                if isinstance(e, (ConsolidationError, ValidationError)):
                    raise
                else:
                    raise ConsolidationError(
                        f"Result consolidation failed: {str(e)}",
                        result_count=len(execution_results),
                        cause=e
                    ) from e

    async def detect_conflicts(
        self,
        execution_results: List[ExecutionResult]
    ) -> List[Dict[str, Any]]:
        """Detect conflicts between agent responses."""
        conflicts = []
        successful_results = [r for r in execution_results if r.success]

        if len(successful_results) < 2:
            return conflicts

        # Simple conflict detection based on response similarity
        # In practice, this would use more sophisticated NLP techniques
        for i, result1 in enumerate(successful_results):
            for j, result2 in enumerate(successful_results[i+1:], i+1):
                # Check for contradictory statements (simplified)
                if self._responses_conflict(result1.response, result2.response):
                    conflict = {
                        "type": "contradictory_information",
                        "description": f"Conflicting responses between {result1.agent_name} and {result2.agent_name}",
                        "agents": [result1.agent_name, result2.agent_name],
                        "agent_ids": [result1.agent_id, result2.agent_id],
                        "responses": [result1.response[:200], result2.response[:200]]
                    }
                    conflicts.append(conflict)

        self.logger.debug(
            "Conflict detection completed",
            conflicts_found=len(conflicts),
            agents_analyzed=len(successful_results)
        )

        return conflicts



    async def synthesize_responses(
        self,
        consolidation_request: ConsolidationRequest,
        context: CoordinationContext,
        workflow_events: Optional[WorkflowEventEmitter] = None
    ) -> ConsolidationResult:
        """Synthesize responses using advanced LLM techniques."""
        try:
            is_streaming = workflow_events is not None

            # Build consolidation prompt
            if workflow_events:
                workflow_events.emit_consolidation_progress(
                    current_step="Building consolidation prompt",
                    progress_percentage=70.0,
                    total_results=len(consolidation_request.execution_results),
                    processed_results=len(consolidation_request.execution_results),
                    consolidation_strategy=consolidation_request.consolidation_strategy.value
                )

            prompt = await self._build_consolidation_prompt(
                consolidation_request.user_message,
                [self._dict_to_result(r) for r in consolidation_request.execution_results]
            )

            # Execute consolidation agent
            if workflow_events:
                workflow_events.emit_consolidation_progress(
                    current_step="Executing consolidation agent",
                    progress_percentage=80.0,
                    total_results=len(consolidation_request.execution_results),
                    processed_results=len(consolidation_request.execution_results),
                    consolidation_strategy=consolidation_request.consolidation_strategy.value
                )

            response = await self._execute_consolidation_agent(
                prompt,
                context,
                workflow_events,
                enable_memory=consolidation_request.enable_memory,
                session_id=consolidation_request.session_id,
                user_id=consolidation_request.user_id,
            )

            # Parse agent response - clean markdown code blocks if present
            if workflow_events:
                workflow_events.emit_consolidation_progress(
                    current_step="Parsing consolidation response",
                    progress_percentage=90.0,
                    total_results=len(consolidation_request.execution_results),
                    processed_results=len(consolidation_request.execution_results),
                    consolidation_strategy=consolidation_request.consolidation_strategy.value
                )

            if is_streaming:
                strategy = consolidation_request.consolidation_strategy or ConsolidationStrategy.SYNTHESIS
                return ConsolidationResult(
                    consolidated_content=response.strip(),
                    consolidation_approach=strategy,
                    confidence_score=consolidation_request.confidence_threshold,
                    key_insights=[],
                    sources_used=[],
                    conflicts_resolved=[],
                    limitations=[]
                )

            cleaned_response = clean_json_response(response)
            consolidation_data = json.loads(cleaned_response)

            # Create conflict resolutions from LLM output
            conflict_resolutions = []
            for conflict_desc in consolidation_data.get("conflicts_resolved", []):
                if conflict_desc.strip():
                    resolution = ConflictResolution(
                        conflict_type="llm_detected",
                        description=conflict_desc,
                        resolution_method="llm_synthesis",
                        affected_agents=consolidation_data.get("sources_used", []),
                        confidence_impact=0.05
                    )
                    conflict_resolutions.append(resolution)

            # Create consolidation result
            result = ConsolidationResult(
                consolidated_content=consolidation_data["consolidated_content"],
                consolidation_approach=ConsolidationStrategy(consolidation_data["consolidation_approach"]),
                confidence_score=consolidation_data["confidence_score"],
                key_insights=consolidation_data.get("key_insights", []),
                sources_used=consolidation_data.get("sources_used", []),
                conflicts_resolved=conflict_resolutions,
                limitations=consolidation_data.get("limitations", [])
            )

            return result

        except json.JSONDecodeError as e:
            raise LLMResponseError(
                f"Failed to parse LLM consolidation response: {str(e)}",
                raw_response=response,
                expected_format="Valid JSON object",
                parsing_errors=[str(e)]
            ) from e

        except Exception as e:
            raise ConsolidationError(
                f"Agent synthesis failed: {str(e)}",
                consolidation_strategy="synthesis",
                cause=e
            ) from e

    async def _build_consolidation_prompt(
        self,
        user_message: str,
        execution_results: List[ExecutionResult]
    ) -> str:
        """Build consolidation prompt for the agent."""
        results_text = format_execution_results(execution_results)

        prompt = f"""USER ORIGINAL REQUEST:
"{user_message}"

AGENT EXECUTION RESULTS:
{results_text}

Please consolidate these agent responses into a single, comprehensive answer that directly addresses the user's request."""

        return prompt

    async def _execute_consolidation_agent(
        self,
        prompt: str,
        context: CoordinationContext,
        workflow_events: Optional[WorkflowEventEmitter] = None,
        *,
        enable_memory: bool = False,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Execute the consolidation agent with optional streaming support."""
        try:
            agent_for_execution = self.consolidation_agent
            if workflow_events:
                # Adjust instruction for streaming-friendly responses while preserving identity
                agent_for_execution = self.consolidation_agent.model_copy()
                agent_for_execution.instruction = get_result_consolidation_instruction(streaming=True)

            # Resolve provider credentials from team context
            creds = getattr(context.team, "llm_provider_credentials", None)
            if not creds:
                raise ConsolidationError(
                    "No LLM provider configured for team; set team.llm_provider_id or agent.llm_provider_id"
                )
            setattr(agent_for_execution, "llm_provider_credentials", creds)
            # Ensure system agent uses team's model (no model in global config)
            agent_for_execution.model = context.team.model

            # Create agent execution request
            request = AgentExecutionRequest(
                message=prompt,
                config={},
                session_id=session_id or f"consolidation_{int(time.time())}",
                user_id=user_id,
                enable_memory=enable_memory,
            )

            # Generate execution ID for tracking
            execution_id = f"consolidation_exec_{int(time.time())}"

            # Execute the consolidation agent with or without streaming
            if workflow_events:
                # Use streaming execution for real-time visibility
                self.logger.info(
                    "Executing consolidation agent with streaming",
                    agent_name=agent_for_execution.name,
                    prompt_length=len(prompt),
                    execution_id=execution_id
                )

                response = await self.agent_service.execute_agent_streaming(
                    agent=agent_for_execution,
                    request=request,
                    auth_headers={},
                    workflow_events=workflow_events,
                    execution_id=execution_id,
                    timeout=60
                )
            else:
                # Use regular execution for backward compatibility
                self.logger.info(
                    "Executing consolidation agent (non-streaming)",
                    agent_name=agent_for_execution.name,
                    prompt_length=len(prompt)
                )

                response = await self.agent_service.execute_agent(
                    agent=agent_for_execution,
                    request=request,
                    auth_headers={}
                )

            if not response.success:
                raise ConsolidationError(
                    f"Consolidation agent failed: {response.error}"
                )

            if not response.content or not response.content.strip():
                raise ConsolidationError(
                    "Consolidation agent returned empty response"
                )

            return response.content.strip()

        except Exception as e:
            self.logger.error(
                "Consolidation agent execution failed",
                error=str(e),
                agent_name=agent_for_execution.name if 'agent_for_execution' in locals() else self.consolidation_agent.name
            )
            raise ConsolidationError(
                f"Consolidation agent execution failed: {str(e)}"
            ) from e

    def select_consolidation_strategy(
        self,
        execution_results: List[ExecutionResult],
        context: CoordinationContext
    ) -> ConsolidationStrategy:
        """Select optimal consolidation strategy based on results."""
        successful_results = [r for r in execution_results if r.success]

        # Single result - no consolidation needed
        if len(successful_results) <= 1:
            return ConsolidationStrategy.BEST_SELECTION

        # Always use LLM synthesis for multiple results
        return ConsolidationStrategy.SYNTHESIS

    def calculate_confidence_score(
        self,
        execution_results: List[ExecutionResult],
        consolidation_result: ConsolidationResult
    ) -> float:
        """Calculate confidence score for consolidated result."""
        successful_results = [r for r in execution_results if r.success]

        if not successful_results:
            return 0.0

        # Base confidence from success rate
        success_rate = len(successful_results) / len(execution_results)
        base_confidence = success_rate * 0.8

        # Adjust for conflicts
        conflict_penalty = len(consolidation_result.conflicts_resolved) * 0.1

        # Adjust for number of sources
        source_bonus = min(0.2, len(successful_results) * 0.05)

        # Calculate final confidence
        final_confidence = base_confidence + source_bonus - conflict_penalty

        return max(0.0, min(1.0, final_confidence))

    def _result_to_dict(self, result: ExecutionResult) -> Dict[str, Any]:
        """Convert ExecutionResult to dictionary for processing."""
        return {
            "agent_id": result.agent_id,
            "agent_name": result.agent_name,
            "question": result.question,
            "response": result.response,
            "success": result.success,
            "execution_time": result.execution_time,
            "error": result.error
        }

    def _dict_to_result(self, data: Dict[str, Any]) -> ExecutionResult:
        """Convert dictionary back to ExecutionResult."""
        from datetime import datetime

        return ExecutionResult(
            execution_id=f"temp_{data['agent_id']}",
            agent_id=data["agent_id"],
            agent_name=data["agent_name"],
            sub_question_id=None,
            question=data["question"],
            response=data["response"],
            success=data["success"],
            execution_time=data["execution_time"],
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            error=data.get("error")
        )

    def _responses_conflict(self, response1: str, response2: str) -> bool:
        """Simple conflict detection between two responses."""
        # This is a simplified implementation
        # In practice, you'd use more sophisticated NLP techniques

        # Check for explicit contradictions
        contradiction_indicators = [
            ("yes", "no"), ("true", "false"), ("correct", "incorrect"),
            ("possible", "impossible"), ("should", "should not"),
            ("can", "cannot"), ("will", "will not")
        ]

        response1_lower = response1.lower()
        response2_lower = response2.lower()

        for pos, neg in contradiction_indicators:
            if pos in response1_lower and neg in response2_lower:
                return True
            if neg in response1_lower and pos in response2_lower:
                return True

        return False

    def _extract_key_points(self, response: str) -> List[str]:
        """Extract key points from a response."""
        # Simplified key point extraction
        # In practice, you'd use more sophisticated NLP techniques

        sentences = response.split('.')
        key_points = []

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and len(sentence) < 200:
                # Filter for sentences that look like key points
                if any(indicator in sentence.lower() for indicator in
                       ["important", "key", "main", "primary", "essential", "critical"]):
                    key_points.append(sentence)
                elif sentence.startswith(("The", "This", "It", "You", "We")):
                    key_points.append(sentence)

        return key_points[:10]  # Limit to top 10 key points
