"""
Main coordination orchestrator implementation.

This module provides the main entry point for the coordination system v2,
orchestrating the complete workflow from query analysis to result consolidation.
"""

import time
from typing import Dict, Optional

from app.core.logging import get_logger
from app.models.internal import CoordinationContext
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from app.runtime.supervisor.infrastructure.services import AIServiceClient, AgentServiceClient

from ..interfaces.query_analyzer import IQueryAnalyzer
from ..interfaces.workflow_planner import IWorkflowPlanner
from ..interfaces.execution_manager import IExecutionManager
from ..interfaces.result_consolidator import IResultConsolidator
from ..models.coordination import CoordinationRequest, CoordinationResponse
from ..configuration.settings import CoordinationConfig, get_coordination_config
from ..exceptions.coordination import CoordinationError, ValidationError
from ..utils.logging import CoordinationLogContext, get_coordination_logger
from ..utils.metrics import get_global_metrics, MetricsCollector
from ..streaming.workflow_events import WorkflowEventEmitter

# Import concrete implementations
from .query_analyzer import LLMQueryAnalyzer
from .workflow_planner import WorkflowPlanner
from .execution_manager import ExecutionManager
from .result_consolidator import LLMResultConsolidator


class CoordinationOrchestrator:
    """
    Main orchestrator for the coordination system v2.
    
    This class coordinates the complete workflow:
    1. Query analysis and agent assignment
    2. Workflow planning and optimization
    3. Multi-agent execution with different patterns
    4. Result consolidation and response synthesis
    
    Features:
    - Dependency injection for all components
    - Comprehensive error handling and recovery
    - Performance monitoring and metrics
    - Configurable behavior and timeouts
    - Structured logging with correlation IDs
    """
    
    def __init__(
        self,
        ai_service_client: "AIServiceClient",
        agent_service_client: "AgentServiceClient",
        config: Optional[CoordinationConfig] = None,
        query_analyzer: Optional[IQueryAnalyzer] = None,
        workflow_planner: Optional[IWorkflowPlanner] = None,
        execution_manager: Optional[IExecutionManager] = None,
        result_consolidator: Optional[IResultConsolidator] = None
    ) -> None:
        """
        Initialize coordination orchestrator with dependencies.
        
        Args:
            ai_service_client: Client for AI service interactions
            agent_service_client: Client for agent service interactions
            config: Configuration settings (uses defaults if not provided)
            query_analyzer: Query analyzer implementation (creates default if not provided)
            workflow_planner: Workflow planner implementation (creates default if not provided)
            execution_manager: Execution manager implementation (creates default if not provided)
            result_consolidator: Result consolidator implementation (creates default if not provided)
        """
        self.ai_service = ai_service_client
        self.agent_service = agent_service_client
        self.config = config or get_coordination_config()
        self.logger = get_coordination_logger("orchestrator")
        
        # Initialize components with dependency injection
        self.query_analyzer = query_analyzer or LLMQueryAnalyzer(
            agent_service_client, self.config.query_analysis
        )
        self.workflow_planner = workflow_planner or WorkflowPlanner(
            self.config.workflow_planning
        )
        self.execution_manager = execution_manager or ExecutionManager(
            agent_service_client, self.config.execution
        )
        self.result_consolidator = result_consolidator or LLMResultConsolidator(
            agent_service_client, self.config.consolidation
        )
        
        self.logger.info(
            "Coordination orchestrator initialized",
            config_version="2.0",
            components_initialized=4
        )
    
    async def coordinate(
        self,
        request: CoordinationRequest,
        workflow_events: Optional[WorkflowEventEmitter] = None
    ) -> CoordinationResponse:
        """
        Coordinate complete multi-agent workflow.
        
        This is the main entry point that orchestrates the entire coordination process:
        1. Query analysis and decomposition
        2. Workflow planning and optimization
        3. Multi-agent execution
        4. Result consolidation
        
        Args:
            request: Coordination request with context and auth headers
            
        Returns:
            CoordinationResponse: Complete response with consolidated results
            
        Raises:
            CoordinationError: When coordination fails
            ValidationError: When input validation fails
        """
        with CoordinationLogContext(request.request_id) as correlation_id:
            with MetricsCollector("full_coordination") as metrics:
                start_time = time.time()
                
                self.logger.info(
                    "Starting coordination workflow",
                    request_id=request.request_id,
                    correlation_id=correlation_id,
                    team_id=request.context.team.id,
                    user_message_length=len(request.context.message),
                    max_agents=request.context.max_agents
                )
                
                try:
                    # Step 1: Query Analysis
                    self.logger.info("Step 1: Starting query analysis")
                    analysis_result = await self.query_analyzer.analyze_query(
                        request.context, request.auth_headers, workflow_events
                    )
                    
                    metrics.add_metadata("selected_agents", len(analysis_result.selected_agent_ids))
                    metrics.add_metadata("workflow_pattern", analysis_result.workflow)
                    metrics.add_metadata("is_complex", analysis_result.is_complex)
                    
                    # Step 2: Workflow Planning
                    self.logger.info("Step 2: Starting workflow planning")
                    workflow_plan = await self.workflow_planner.create_workflow_plan(
                        analysis_result, request.context
                    )
                    
                    metrics.add_metadata("execution_plan_created", True)
                    metrics.add_metadata("estimated_time", workflow_plan.estimated_time)
                    
                    # Step 3: Workflow Execution
                    self.logger.info("Step 3: Starting workflow execution")
                    execution_results = await self.execution_manager.execute_workflow(
                        workflow_plan, request.auth_headers, workflow_events
                    )
                    
                    successful_executions = sum(1 for r in execution_results if r.success)
                    metrics.add_metadata("successful_executions", successful_executions)
                    metrics.add_metadata("total_executions", len(execution_results))
                    
                    # Step 4: Result Consolidation
                    self.logger.info("Step 4: Starting result consolidation")
                    consolidation_result = await self.result_consolidator.consolidate_results(
                        execution_results, request.context, workflow_events=workflow_events
                    )
                    
                    metrics.add_metadata("consolidation_confidence", consolidation_result.confidence_score)
                    metrics.add_metadata("conflicts_resolved", len(consolidation_result.conflicts_resolved))
                    
                    # Build final response
                    total_time = time.time() - start_time
                    response = self._build_success_response(
                        request, analysis_result, execution_results, 
                        consolidation_result, total_time
                    )
                    
                    # Record global metrics
                    global_metrics = get_global_metrics()
                    global_metrics.record_request(True)
                    
                    self.logger.info(
                        "Coordination workflow completed successfully",
                        request_id=request.request_id,
                        total_time=total_time,
                        selected_agents=len(analysis_result.selected_agent_ids),
                        successful_executions=successful_executions,
                        consolidation_confidence=consolidation_result.confidence_score
                    )
                    
                    return response
                    
                except Exception as e:
                    total_time = time.time() - start_time
                    
                    # Record failure metrics
                    global_metrics = get_global_metrics()
                    global_metrics.record_request(False)
                    
                    self.logger.error(
                        "Coordination workflow failed",
                        request_id=request.request_id,
                        error=str(e),
                        error_type=type(e).__name__,
                        total_time=total_time
                    )
                    
                    # Build error response
                    error_response = self._build_error_response(request, str(e), total_time)
                    
                    # Re-raise coordination errors, wrap others
                    if isinstance(e, (CoordinationError, ValidationError)):
                        return error_response
                    else:
                        return error_response
    
    def _build_success_response(
        self,
        request: CoordinationRequest,
        analysis_result,
        execution_results,
        consolidation_result,
        total_time: float
    ) -> CoordinationResponse:
        """Build successful coordination response."""
        return CoordinationResponse(
            success=True,
            request_id=request.request_id,
            message="Coordination completed successfully",
            consolidated_response=consolidation_result.consolidated_content,
            execution_results=execution_results,
            metadata={
                "total_execution_time": total_time,
                "workflow_pattern": analysis_result.workflow,
                "agents_consulted": len(analysis_result.selected_agent_ids),
                "successful_agents": sum(1 for r in execution_results if r.success),
                "consolidation_strategy": consolidation_result.consolidation_approach.value,
                "confidence_score": consolidation_result.confidence_score,
                "conflicts_resolved": len(consolidation_result.conflicts_resolved),
                "key_insights": consolidation_result.key_insights,
                "sources_used": consolidation_result.sources_used,
                "limitations": consolidation_result.limitations,
                "is_complex_query": analysis_result.is_complex,
                "sub_questions_count": len(analysis_result.sub_questions)
            }
        )
    
    def _build_error_response(
        self,
        request: CoordinationRequest,
        error_message: str,
        total_time: float
    ) -> CoordinationResponse:
        """Build error coordination response."""
        return CoordinationResponse(
            success=False,
            request_id=request.request_id,
            message="Coordination failed",
            consolidated_response="I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists.",
            execution_results=[],
            metadata={
                "total_execution_time": total_time,
                "error_occurred": True,
                "agents_consulted": 0,
                "successful_agents": 0
            },
            error=error_message
        )
