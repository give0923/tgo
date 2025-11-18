"""
Execution management implementation.

This module provides the concrete implementation for executing workflow plans
with different patterns and managing multi-agent coordination.
"""

import asyncio
import time
from typing import List, Dict, Optional, AsyncIterator, TYPE_CHECKING
from datetime import datetime

from app.core.logging import get_logger
from app.models.internal import CoordinationContext, AgentExecutionRequest, AgentExecutionResponse

if TYPE_CHECKING:  # pragma: no cover
    from app.runtime.supervisor.infrastructure.services import AgentServiceClient

from ..interfaces.execution_manager import IExecutionManager
from ..models.execution import (
    WorkflowPlan, ExecutionResult, ExecutionStatus, AgentExecution, WorkflowPattern
)
from ..configuration.settings import ExecutionConfig
from ..exceptions.coordination import ExecutionError, TimeoutError, AgentNotFoundError
from ..utils.logging import get_coordination_logger
from ..utils.metrics import MetricsCollector
from ..streaming.workflow_events import WorkflowEventEmitter


class ExecutionManager(IExecutionManager):
    """
    Execution manager that coordinates multi-agent workflow execution.
    
    This implementation:
    - Executes workflows with different patterns (parallel, sequential, hierarchical)
    - Manages agent lifecycle and status tracking
    - Handles timeouts, retries, and error recovery
    - Provides real-time progress monitoring
    - Collects and aggregates execution results
    """
    
    def __init__(
        self,
        agent_service_client: "AgentServiceClient",
        config: ExecutionConfig
    ) -> None:
        self.agent_service = agent_service_client
        self.config = config
        self.logger = get_coordination_logger("execution_manager")
        
        # Track active executions for monitoring and cancellation
        self.active_executions: Dict[str, WorkflowPlan] = {}
        self.execution_status: Dict[str, Dict[str, ExecutionStatus]] = {}
    
    async def execute_workflow(
        self,
        workflow_plan: WorkflowPlan,
        auth_headers: Dict[str, str],
        workflow_events: Optional[WorkflowEventEmitter] = None
    ) -> List[ExecutionResult]:
        """Execute complete workflow plan and return results."""
        with MetricsCollector("workflow_execution", {"pattern": workflow_plan.pattern.value}) as metrics:
            self.logger.info(
                "Starting workflow execution",
                plan_id=workflow_plan.plan_id,
                pattern=workflow_plan.pattern.value,
                agent_count=workflow_plan.total_agents,
                estimated_time=workflow_plan.estimated_time
            )
            
            # Register active execution
            self.active_executions[workflow_plan.plan_id] = workflow_plan
            self.execution_status[workflow_plan.plan_id] = {
                exec.agent_id: ExecutionStatus.PENDING for exec in workflow_plan.agent_executions
            }
            
            try:
                # Execute based on pattern
                if workflow_plan.pattern == WorkflowPattern.SINGLE:
                    results = await self._execute_single(workflow_plan, auth_headers, workflow_events)
                elif workflow_plan.pattern == WorkflowPattern.PARALLEL:
                    results = await self.execute_parallel(workflow_plan, auth_headers, workflow_events)
                elif workflow_plan.pattern == WorkflowPattern.SEQUENTIAL:
                    results = await self.execute_sequential(workflow_plan, auth_headers, workflow_events)
                elif workflow_plan.pattern == WorkflowPattern.HIERARCHICAL:
                    results = await self.execute_hierarchical(workflow_plan, auth_headers, workflow_events)
                elif workflow_plan.pattern == WorkflowPattern.PIPELINE:
                    results = await self._execute_pipeline(workflow_plan, auth_headers, workflow_events)
                else:
                    raise ExecutionError(
                        f"Unsupported workflow pattern: {workflow_plan.pattern}",
                        execution_pattern=workflow_plan.pattern.value
                    )
                
                # Update metrics
                successful_count = sum(1 for r in results if r.success)
                failed_count = len(results) - successful_count
                
                metrics.add_metadata("successful_agents", successful_count)
                metrics.add_metadata("failed_agents", failed_count)
                metrics.add_metadata("total_agents", len(results))
                
                self.logger.info(
                    "Workflow execution completed",
                    plan_id=workflow_plan.plan_id,
                    successful_agents=successful_count,
                    failed_agents=failed_count,
                    total_agents=len(results)
                )
                
                return results
                
            except Exception as e:
                self.logger.error(
                    "Workflow execution failed",
                    plan_id=workflow_plan.plan_id,
                    error=str(e),
                    error_type=type(e).__name__
                )
                
                if isinstance(e, (ExecutionError, TimeoutError)):
                    raise
                else:
                    raise ExecutionError(
                        f"Workflow execution failed: {str(e)}",
                        execution_pattern=workflow_plan.pattern.value,
                        cause=e
                    ) from e
            
            finally:
                # Clean up active execution tracking
                self.active_executions.pop(workflow_plan.plan_id, None)
                self.execution_status.pop(workflow_plan.plan_id, None)
    
    async def execute_parallel(
        self,
        workflow_plan: WorkflowPlan,
        auth_headers: Dict[str, str],
        workflow_events: Optional[WorkflowEventEmitter] = None
    ) -> List[ExecutionResult]:
        """Execute multiple agents in parallel."""
        executions = workflow_plan.agent_executions
        timeout = workflow_plan.timeout

        self.logger.info(
            "Starting parallel execution",
            agent_count=len(executions),
            timeout=timeout or self.config.default_timeout
        )

        # Emit batch execution started event
        if workflow_events:
            workflow_events.emit_batch_execution_started("parallel", len(executions))

        # Create tasks for all executions
        self.logger.debug("Creating parallel execution tasks", task_count=len(executions))
        tasks = []
        for execution in executions:
            task = asyncio.create_task(
                self._execute_single_agent(execution, workflow_plan, auth_headers, timeout, workflow_events)
            )
            tasks.append(task)
        
        try:
            # Wait for all tasks to complete
            execution_timeout = timeout or self.config.default_timeout
            self.logger.debug(
                "Waiting for parallel executions",
                timeout=execution_timeout,
                task_count=len(tasks)
            )
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=execution_timeout
            )
            
            # Process results and handle exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create error result for failed execution
                    execution = executions[i]
                    error_result = ExecutionResult(
                        execution_id=f"exec_{execution.agent_id}_{int(time.time())}",
                        agent_id=execution.agent_id,
                        agent_name=execution.agent_name,
                        sub_question_id=execution.sub_question_id,
                        question=execution.question,
                        response="",
                        success=False,
                        execution_time=0.0,
                        start_time=datetime.utcnow(),
                        end_time=datetime.utcnow(),
                        error=str(result)
                    )
                    processed_results.append(error_result)
                else:
                    processed_results.append(result)

            # Emit batch execution progress event
            if workflow_events:
                completed_agents = sum(1 for r in processed_results if r.success)
                failed_agents = len(processed_results) - completed_agents
                workflow_events.emit_batch_execution_progress(
                    "parallel", len(executions), completed_agents, failed_agents
                )

            return processed_results
            
        except asyncio.TimeoutError:
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            raise TimeoutError(
                f"Parallel execution timed out after {execution_timeout} seconds",
                timeout_seconds=execution_timeout,
                operation_type="parallel_execution"
            )
    
    async def execute_sequential(
        self,
        workflow_plan: WorkflowPlan,
        auth_headers: Dict[str, str],
        workflow_events: Optional[WorkflowEventEmitter] = None
    ) -> List[ExecutionResult]:
        """Execute agents sequentially with result chaining."""
        executions = workflow_plan.agent_executions
        timeout = workflow_plan.timeout

        self.logger.debug(
            "Starting sequential execution",
            agent_count=len(executions),
            timeout=timeout or self.config.default_timeout
        )

        # Emit batch execution started event
        if workflow_events:
            workflow_events.emit_batch_execution_started("sequential", len(executions))

        results = []
        current_context = ""
        
        for i, execution in enumerate(executions):
            # For sequential execution, pass previous results as context
            if i > 0 and results:
                previous_result = results[-1]
                if previous_result.success:
                    current_context = f"Previous result: {previous_result.response}\n\n"
                    # Update question with context
                    execution.question = current_context + execution.question
            
            try:
                result = await self._execute_single_agent(execution, workflow_plan, auth_headers, timeout, workflow_events)
                results.append(result)
                
                # If execution failed and we're in sequential mode, decide whether to continue
                if not result.success:
                    self.logger.warning(
                        "Sequential execution step failed",
                        step=i+1,
                        agent_id=execution.agent_id,
                        error=result.error
                    )
                    # For now, continue with remaining agents
                    # In practice, you might want to make this configurable
                
            except Exception as e:
                # Create error result and continue
                error_result = ExecutionResult(
                    execution_id=f"exec_{execution.agent_id}_{int(time.time())}",
                    agent_id=execution.agent_id,
                    agent_name=execution.agent_name,
                    sub_question_id=execution.sub_question_id,
                    question=execution.question,
                    response="",
                    success=False,
                    execution_time=0.0,
                    start_time=datetime.utcnow(),
                    end_time=datetime.utcnow(),
                    error=str(e)
                )
                results.append(error_result)
        
        return results
    
    async def execute_hierarchical(
        self,
        workflow_plan: WorkflowPlan,
        auth_headers: Dict[str, str],
        workflow_events: Optional[WorkflowEventEmitter] = None
    ) -> List[ExecutionResult]:
        """Execute agents in hierarchical pattern."""
        executions = workflow_plan.agent_executions
        hierarchy_levels = workflow_plan.parallel_groups
        timeout = workflow_plan.timeout

        self.logger.debug(
            "Starting hierarchical execution",
            agent_count=len(executions),
            hierarchy_levels=len(hierarchy_levels),
            timeout=timeout or self.config.default_timeout
        )
        
        # Create execution lookup
        execution_map = {exec.agent_id: exec for exec in executions}
        all_results = []
        level_context = ""
        
        for level_num, agent_ids in enumerate(hierarchy_levels):
            self.logger.debug(
                "Executing hierarchy level",
                level=level_num + 1,
                agents_in_level=len(agent_ids)
            )
            
            # Get executions for this level
            level_executions = []
            for agent_id in agent_ids:
                if agent_id in execution_map:
                    execution = execution_map[agent_id]
                    # Add context from previous levels
                    if level_context:
                        execution.question = f"{level_context}\n\n{execution.question}"
                    level_executions.append(execution)
            
            # Execute this level in parallel
            # Create a temporary workflow plan for this level
            from ..models.execution import WorkflowPlan, WorkflowPattern
            level_plan = WorkflowPlan(
                plan_id=f"{workflow_plan.plan_id}_level_{level_num}",
                pattern=WorkflowPattern.PARALLEL,
                agent_executions=level_executions,
                context=workflow_plan.context,
                timeout=timeout
            )
            level_results = await self.execute_parallel(level_plan, auth_headers)
            
            all_results.extend(level_results)
            
            # Build context for next level from successful results
            successful_results = [r for r in level_results if r.success]
            if successful_results:
                level_context = "Previous level results:\n" + "\n".join(
                    f"- {r.agent_name}: {r.response[:200]}..." 
                    for r in successful_results
                )
        
        return all_results

    async def monitor_execution_progress(
        self,
        workflow_plan: WorkflowPlan
    ) -> AsyncIterator[Dict[str, ExecutionStatus]]:
        """Monitor execution progress in real-time."""
        plan_id = workflow_plan.plan_id

        while plan_id in self.execution_status:
            current_status = self.execution_status[plan_id].copy()
            yield current_status

            # Check if all executions are complete
            if all(status.value in ["completed", "failed", "timeout", "cancelled"]
                   for status in current_status.values()):
                break

            # Wait before next check
            await asyncio.sleep(1.0)

    async def cancel_execution(
        self,
        workflow_plan: WorkflowPlan
    ) -> bool:
        """Cancel ongoing workflow execution."""
        plan_id = workflow_plan.plan_id

        if plan_id not in self.active_executions:
            self.logger.warning(
                "Cannot cancel execution - plan not found",
                plan_id=plan_id
            )
            return False

        # Update status to cancelled
        if plan_id in self.execution_status:
            for agent_id in self.execution_status[plan_id]:
                if self.execution_status[plan_id][agent_id] in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]:
                    self.execution_status[plan_id][agent_id] = ExecutionStatus.CANCELLED

        self.logger.info(
            "Workflow execution cancelled",
            plan_id=plan_id
        )

        return True

    async def _execute_single(
        self,
        workflow_plan: WorkflowPlan,
        auth_headers: Dict[str, str],
        workflow_events: Optional[WorkflowEventEmitter] = None
    ) -> List[ExecutionResult]:
        """Execute single agent workflow."""
        if not workflow_plan.agent_executions:
            raise ExecutionError("No agent executions in single workflow plan")

        execution = workflow_plan.agent_executions[0]
        result = await self._execute_single_agent(execution, workflow_plan, auth_headers, workflow_plan.timeout, workflow_events)
        return [result]

    async def _execute_pipeline(
        self,
        workflow_plan: WorkflowPlan,
        auth_headers: Dict[str, str],
        workflow_events: Optional[WorkflowEventEmitter] = None
    ) -> List[ExecutionResult]:
        """Execute pipeline workflow with data flow between agents."""
        # Pipeline is similar to sequential but with more sophisticated data passing
        # For now, implement as sequential with enhanced context passing
        return await self.execute_sequential(workflow_plan, auth_headers, workflow_events)

    async def _execute_single_agent(
        self,
        execution: AgentExecution,
        workflow_plan: WorkflowPlan,
        auth_headers: Dict[str, str],
        timeout: Optional[int] = None,
        workflow_events: Optional[WorkflowEventEmitter] = None
    ) -> ExecutionResult:
        """Execute a single agent and return result."""
        execution_id = f"exec_{execution.agent_id}_{int(time.time())}"
        start_time = datetime.utcnow()

        # Update execution status
        self._update_execution_status(execution.agent_id, ExecutionStatus.RUNNING)

        # Emit agent execution started event
        if workflow_events:
            workflow_events.emit_agent_execution_started(
                execution.agent_id,
                execution.agent_name,
                execution_id,
                execution.question
            )
        self.logger.info(
            "Executing single agent",
            execution_id=execution_id,
            agent_id=execution.agent_id,
            agent_name=execution.agent_name,
            question_length=len(execution.question)
        )

        try:
            # Get the agent object from the team context
            agent = None
            for team_agent in workflow_plan.context.team.agents:
                if str(team_agent.id) == str(execution.agent_id):
                    agent = team_agent
                    break

            if not agent:
                raise ExecutionError(
                    f"Agent {execution.agent_id} not found in team context",
                    agent_id=execution.agent_id
                )

            self.logger.debug("Agent found for execution", agent_name=agent.name, agent_id=execution.agent_id)

            # Create agent execution request
            session_id = workflow_plan.context.session_id or f"coord_{execution_id}"
            user_id = workflow_plan.context.user_id
            request = AgentExecutionRequest(
                message=execution.question,
                config={},
                session_id=session_id,
                user_id=user_id,
                enable_memory=workflow_plan.context.enable_memory,
            )

            # Execute agent with or without streaming
            self.logger.debug(
                "Executing agent with context",
                mcp_url=workflow_plan.context.mcp_url,
                rag_url=workflow_plan.context.rag_url,
                agent_id=execution.agent_id
            )

            if workflow_events:
                # Use streaming execution
                response = await self.agent_service.execute_agent_streaming(
                    agent=agent,
                    request=request,
                    auth_headers=auth_headers,
                    workflow_events=workflow_events,
                    execution_id=execution_id,
                    timeout=timeout,
                    mcp_url=workflow_plan.context.mcp_url,
                    rag_url=workflow_plan.context.rag_url,
                    rag_api_key=workflow_plan.context.rag_api_key
                )
            else:
                # Use regular execution
                response = await self.agent_service.execute_agent(
                    agent=agent,
                    request=request,
                    auth_headers=auth_headers,
                    timeout=timeout,
                    mcp_url=workflow_plan.context.mcp_url,
                    rag_url=workflow_plan.context.rag_url,
                    rag_api_key=workflow_plan.context.rag_api_key
                )

            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()

            # Create execution result
            result = ExecutionResult(
                execution_id=execution_id,
                agent_id=execution.agent_id,
                agent_name=execution.agent_name,
                sub_question_id=execution.sub_question_id,
                question=execution.question,
                response=response.content if response.success else "",
                success=response.success,
                execution_time=execution_time,
                start_time=start_time,
                end_time=end_time,
                error=response.error if not response.success else None,
                metadata={
                    "agent_execution_time": response.execution_time if hasattr(response, 'execution_time') else execution_time,
                    "tokens_used": response.tokens_used if hasattr(response, 'tokens_used') else 0
                }
            )

            # Update execution status
            final_status = ExecutionStatus.COMPLETED if response.success else ExecutionStatus.FAILED
            self._update_execution_status(execution.agent_id, final_status)

            # Emit agent execution completed event
            if workflow_events:
                workflow_events.emit_agent_execution_completed(result)

            self.logger.debug(
                "Agent execution completed",
                execution_id=execution_id,
                agent_id=execution.agent_id,
                success=response.success,
                execution_time=execution_time
            )

            return result

        except asyncio.TimeoutError:
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()

            self._update_execution_status(execution.agent_id, ExecutionStatus.TIMEOUT)

            return ExecutionResult(
                execution_id=execution_id,
                agent_id=execution.agent_id,
                agent_name=execution.agent_name,
                sub_question_id=execution.sub_question_id,
                question=execution.question,
                response="",
                success=False,
                execution_time=execution_time,
                start_time=start_time,
                end_time=end_time,
                error=f"Agent execution timed out after {timeout or self.config.agent_timeout} seconds"
            )

        except Exception as e:
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()

            self._update_execution_status(execution.agent_id, ExecutionStatus.FAILED)

            self.logger.error(
                "Agent execution failed",
                execution_id=execution_id,
                agent_id=execution.agent_id,
                error=str(e),
                error_type=type(e).__name__
            )

            return ExecutionResult(
                execution_id=execution_id,
                agent_id=execution.agent_id,
                agent_name=execution.agent_name,
                sub_question_id=execution.sub_question_id,
                question=execution.question,
                response="",
                success=False,
                execution_time=execution_time,
                start_time=start_time,
                end_time=end_time,
                error=str(e)
            )

    def _update_execution_status(self, agent_id: str, status: ExecutionStatus) -> None:
        """Update execution status for monitoring."""
        for plan_id, agent_statuses in self.execution_status.items():
            if agent_id in agent_statuses:
                agent_statuses[agent_id] = status
                break
