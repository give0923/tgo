"""
Workflow planning implementation.

This module provides the concrete implementation for creating executable
workflow plans from query analysis results with optimization and validation.
"""

import time
from typing import List, Dict, Set, Tuple
from collections import defaultdict, deque

from app.core.logging import get_logger
from app.models.internal import CoordinationContext, Agent

from ..interfaces.workflow_planner import IWorkflowPlanner
from ..models.coordination import QueryAnalysisResult, WorkflowType
from ..models.execution import WorkflowPlan, AgentExecution, WorkflowPattern, ExecutionStatus
from ..configuration.settings import WorkflowPlanningConfig
from ..exceptions.coordination import WorkflowPlanningError, DependencyError, ValidationError
from ..utils.validation import validate_workflow_plan
from ..utils.logging import get_coordination_logger
from ..utils.metrics import MetricsCollector


class WorkflowPlanner(IWorkflowPlanner):
    """
    Workflow planner that creates optimized execution plans.
    
    This implementation:
    - Converts query analysis results into executable plans
    - Optimizes execution order for maximum parallelization
    - Resolves dependencies and detects cycles
    - Validates plan feasibility and constraints
    - Provides accurate time estimates
    """
    
    def __init__(self, config: WorkflowPlanningConfig) -> None:
        self.config = config
        self.logger = get_coordination_logger("workflow_planner")
    
    async def create_workflow_plan(
        self,
        analysis_result: QueryAnalysisResult,
        context: CoordinationContext
    ) -> WorkflowPlan:
        """Create executable workflow plan from query analysis."""
        with MetricsCollector("workflow_planning") as metrics:
            self.logger.info(
                "Creating workflow plan",
                workflow_pattern=analysis_result.workflow,
                selected_agents=len(analysis_result.selected_agent_ids),
                is_complex=analysis_result.is_complex,
                sub_questions=len(analysis_result.sub_questions)
            )
            
            try:
                # Create agent executions from analysis result
                agent_executions = await self._create_agent_executions(
                    analysis_result, context
                )
                
                # Optimize execution order if enabled
                parallel_groups = analysis_result.execution_plan.parallel_groups
                if self.config.enable_optimization:
                    parallel_groups = await self.optimize_execution_order(
                        agent_executions,
                        analysis_result.execution_plan.dependencies
                    )
                
                # Create workflow plan
                workflow_plan = WorkflowPlan(
                    plan_id="",  # Will be auto-generated
                    pattern=WorkflowPattern(analysis_result.workflow),
                    agent_executions=agent_executions,
                    context=context,
                    dependencies=analysis_result.execution_plan.dependencies,
                    parallel_groups=parallel_groups,
                    estimated_time=analysis_result.execution_plan.estimated_time,
                    timeout=min(context.timeout, self.config.default_timeout)
                )
                
                # Validate the plan
                await self.validate_plan(workflow_plan, context)
                
                # Update time estimate
                workflow_plan.estimated_time = self.estimate_execution_time(workflow_plan)
                
                metrics.add_metadata("agent_count", len(agent_executions))
                metrics.add_metadata("pattern", analysis_result.workflow)
                
                self.logger.info(
                    "Workflow plan created successfully",
                    plan_id=workflow_plan.plan_id,
                    pattern=workflow_plan.pattern.value,
                    agent_count=workflow_plan.total_agents,
                    estimated_time=workflow_plan.estimated_time,
                    parallel_groups=len(workflow_plan.parallel_groups)
                )
                
                return workflow_plan
                
            except Exception as e:
                self.logger.error(
                    "Workflow plan creation failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    workflow_pattern=analysis_result.workflow
                )
                
                if isinstance(e, (WorkflowPlanningError, ValidationError, DependencyError)):
                    raise
                else:
                    raise WorkflowPlanningError(
                        f"Failed to create workflow plan: {str(e)}",
                        workflow_pattern=analysis_result.workflow,
                        agent_count=len(analysis_result.selected_agent_ids),
                        cause=e
                    ) from e
    
    async def optimize_execution_order(
        self,
        executions: List[AgentExecution],
        dependencies: List[str]
    ) -> List[List[str]]:
        """Optimize execution order for maximum parallelization."""
        self.logger.debug(
            "Optimizing execution order",
            execution_count=len(executions),
            dependency_count=len(dependencies)
        )
        
        try:
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(executions, dependencies)
            
            # Detect cycles
            if self.config.detect_cycles:
                cycles = self._detect_cycles(dependency_graph)
                if cycles:
                    raise DependencyError(
                        f"Circular dependencies detected: {cycles}",
                        circular_dependencies=cycles
                    )
            
            # Perform topological sort to find optimal grouping
            parallel_groups = self._topological_sort_with_parallelization(
                executions, dependency_graph
            )
            
            self.logger.debug(
                "Execution order optimized",
                parallel_groups_count=len(parallel_groups),
                max_parallel_agents=max(len(group) for group in parallel_groups) if parallel_groups else 0
            )
            
            return parallel_groups
            
        except Exception as e:
            if isinstance(e, DependencyError):
                raise
            else:
                raise DependencyError(
                    f"Failed to optimize execution order: {str(e)}",
                    cause=e
                ) from e
    
    async def validate_plan(
        self,
        plan: WorkflowPlan,
        context: CoordinationContext
    ) -> bool:
        """Validate workflow plan for feasibility and consistency."""
        try:
            validation_errors = validate_workflow_plan(plan, context)
            
            if validation_errors:
                raise ValidationError(
                    f"Workflow plan validation failed: {'; '.join(validation_errors)}",
                    validation_errors=validation_errors
                )
            
            # Additional business logic validation
            self._validate_business_constraints(plan, context)
            
            self.logger.debug(
                "Workflow plan validation passed",
                plan_id=plan.plan_id,
                agent_count=plan.total_agents
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                "Workflow plan validation failed",
                error=str(e),
                plan_id=plan.plan_id if hasattr(plan, 'plan_id') else 'unknown'
            )
            raise
    
    def estimate_execution_time(self, plan: WorkflowPlan) -> float:
        """Estimate total execution time for the workflow plan."""
        if not plan.agent_executions:
            return 0.0
        
        # Base time per agent (configurable)
        base_time_per_agent = 15.0
        
        if plan.pattern == WorkflowPattern.SINGLE:
            return base_time_per_agent
        
        elif plan.pattern == WorkflowPattern.PARALLEL:
            # Parallel execution time is the maximum of any single agent
            return base_time_per_agent * 1.2  # Small overhead for coordination
        
        elif plan.pattern == WorkflowPattern.SEQUENTIAL:
            # Sequential execution is sum of all agents
            return base_time_per_agent * len(plan.agent_executions)
        
        elif plan.pattern == WorkflowPattern.HIERARCHICAL:
            # Hierarchical is based on levels
            levels = len(plan.parallel_groups) if plan.parallel_groups else 1
            return base_time_per_agent * levels * 1.5  # Overhead for coordination
        
        elif plan.pattern == WorkflowPattern.PIPELINE:
            # Pipeline is sequential with some overlap
            return base_time_per_agent * len(plan.agent_executions) * 0.8
        
        else:
            # Default fallback
            return base_time_per_agent * len(plan.agent_executions)
    
    async def _create_agent_executions(
        self,
        analysis_result: QueryAnalysisResult,
        context: CoordinationContext
    ) -> List[AgentExecution]:
        """Create agent executions from analysis result."""
        agent_executions = []
        
        # Get available agents for lookup
        available_agents = {str(agent.id): agent for agent in context.team.agents}
        
        if analysis_result.is_complex and analysis_result.sub_questions:
            # Create executions from sub-questions
            for sub_question in analysis_result.sub_questions:
                agent = available_agents.get(sub_question.assigned_agent_id)
                if not agent:
                    raise WorkflowPlanningError(
                        f"Agent {sub_question.assigned_agent_id} not found in available agents",
                        agent_count=len(available_agents)
                    )
                
                execution = AgentExecution(
                    agent_id=str(agent.id),
                    agent_name=agent.name,
                    sub_question_id=sub_question.id,
                    question=sub_question.question
                )
                agent_executions.append(execution)
        
        else:
            # Create executions for simple queries
            for agent_id in analysis_result.selected_agent_ids:
                agent = available_agents.get(agent_id)
                if not agent:
                    raise WorkflowPlanningError(
                        f"Agent {agent_id} not found in available agents",
                        agent_count=len(available_agents)
                    )
                
                execution = AgentExecution(
                    agent_id=str(agent.id),
                    agent_name=agent.name,
                    sub_question_id=None,
                    question=context.message  # Use original message for simple queries
                )
                agent_executions.append(execution)
        
        return agent_executions
    
    def _build_dependency_graph(
        self,
        executions: List[AgentExecution],
        dependencies: List[str]
    ) -> Dict[str, Set[str]]:
        """Build dependency graph from executions and dependencies."""
        graph = defaultdict(set)
        
        # Initialize all agents in graph
        for execution in executions:
            graph[execution.agent_id] = set()
        
        # Add dependencies (simplified - in practice would parse dependency strings)
        # For now, assume dependencies are in format "agent1->agent2"
        for dep in dependencies:
            if "->" in dep:
                prerequisite, dependent = dep.split("->", 1)
                prerequisite = prerequisite.strip()
                dependent = dependent.strip()
                
                if prerequisite in graph and dependent in graph:
                    graph[dependent].add(prerequisite)
        
        return dict(graph)
    
    def _detect_cycles(self, graph: Dict[str, Set[str]]) -> List[str]:
        """Detect cycles in dependency graph using DFS."""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycles.append(" -> ".join(path[cycle_start:] + [node]))
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, set()):
                if dfs(neighbor, path):
                    return True
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _topological_sort_with_parallelization(
        self,
        executions: List[AgentExecution],
        graph: Dict[str, Set[str]]
    ) -> List[List[str]]:
        """Perform topological sort with parallelization optimization."""
        # Calculate in-degrees
        in_degree = {exec.agent_id: len(graph.get(exec.agent_id, set())) for exec in executions}
        
        parallel_groups = []
        
        while in_degree:
            # Find all nodes with in-degree 0 (can be executed in parallel)
            current_group = [agent_id for agent_id, degree in in_degree.items() if degree == 0]
            
            if not current_group:
                # This shouldn't happen if there are no cycles
                remaining = list(in_degree.keys())
                raise DependencyError(
                    "Cannot resolve dependencies - possible cycle detected",
                    missing_dependencies=remaining
                )
            
            parallel_groups.append(current_group)
            
            # Remove current group from graph and update in-degrees
            for agent_id in current_group:
                del in_degree[agent_id]
                
                # Update in-degrees of dependent nodes
                for other_agent, deps in graph.items():
                    if agent_id in deps and other_agent in in_degree:
                        in_degree[other_agent] -= 1
        
        return parallel_groups
    
    def _validate_business_constraints(
        self,
        plan: WorkflowPlan,
        context: CoordinationContext
    ) -> None:
        """Validate business-specific constraints."""
        # Check parallel agent limits
        max_parallel = max(len(group) for group in plan.parallel_groups) if plan.parallel_groups else 1
        if max_parallel > self.config.max_parallel_agents:
            raise ValidationError(
                f"Plan requires {max_parallel} parallel agents, exceeds limit of {self.config.max_parallel_agents}",
                field_name="parallel_agents",
                field_value=max_parallel,
                validation_rule=f"max_parallel_agents <= {self.config.max_parallel_agents}"
            )
        
        # Check sequential depth for sequential patterns
        if plan.pattern == WorkflowPattern.SEQUENTIAL:
            if len(plan.agent_executions) > self.config.max_sequential_depth:
                raise ValidationError(
                    f"Sequential plan depth {len(plan.agent_executions)} exceeds limit of {self.config.max_sequential_depth}",
                    field_name="sequential_depth",
                    field_value=len(plan.agent_executions),
                    validation_rule=f"sequential_depth <= {self.config.max_sequential_depth}"
                )
        
        # Check hierarchical levels
        if plan.pattern == WorkflowPattern.HIERARCHICAL:
            levels = len(plan.parallel_groups) if plan.parallel_groups else 1
            if levels > self.config.max_hierarchical_levels:
                raise ValidationError(
                    f"Hierarchical plan levels {levels} exceeds limit of {self.config.max_hierarchical_levels}",
                    field_name="hierarchical_levels",
                    field_value=levels,
                    validation_rule=f"hierarchical_levels <= {self.config.max_hierarchical_levels}"
                )
