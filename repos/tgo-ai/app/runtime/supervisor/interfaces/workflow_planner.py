"""
Interface for workflow planning component.

This interface defines the contract for creating executable
workflow plans from query analysis results.
"""

from abc import ABC, abstractmethod
from typing import List

from app.models.internal import CoordinationContext
from ..models.coordination import QueryAnalysisResult
from ..models.execution import WorkflowPlan, AgentExecution


class IWorkflowPlanner(ABC):
    """
    Interface for workflow planning and execution plan creation.
    
    This component is responsible for:
    1. Converting query analysis results into executable plans
    2. Resolving agent dependencies and constraints
    3. Optimizing execution order and parallelization
    4. Creating detailed execution timelines
    5. Validating plan feasibility
    """
    
    @abstractmethod
    async def create_workflow_plan(
        self,
        analysis_result: QueryAnalysisResult,
        context: CoordinationContext
    ) -> WorkflowPlan:
        """
        Create executable workflow plan from query analysis.
        
        This method:
        - Maps sub-questions to agent executions
        - Resolves dependencies between agents
        - Optimizes parallel execution groups
        - Sets appropriate timeouts and constraints
        - Validates plan feasibility
        
        Args:
            analysis_result: Result from query analysis
            context: Coordination context
            
        Returns:
            WorkflowPlan: Executable workflow plan
            
        Raises:
            WorkflowPlanningError: When plan creation fails
            DependencyError: When dependencies cannot be resolved
            ValidationError: When plan validation fails
        """
        pass
    
    @abstractmethod
    async def optimize_execution_order(
        self,
        executions: List[AgentExecution],
        dependencies: List[str]
    ) -> List[List[str]]:
        """
        Optimize execution order for maximum parallelization.
        
        Args:
            executions: List of agent executions
            dependencies: List of dependency constraints
            
        Returns:
            List of parallel execution groups (agent IDs)
            
        Raises:
            DependencyError: When dependencies create cycles
        """
        pass
    
    @abstractmethod
    async def validate_plan(
        self,
        plan: WorkflowPlan,
        context: CoordinationContext
    ) -> bool:
        """
        Validate workflow plan for feasibility and consistency.
        
        Args:
            plan: Workflow plan to validate
            context: Coordination context
            
        Returns:
            bool: True if plan is valid and executable
            
        Raises:
            ValidationError: When validation fails
        """
        pass
    
    @abstractmethod
    def estimate_execution_time(
        self,
        plan: WorkflowPlan
    ) -> float:
        """
        Estimate total execution time for the workflow plan.
        
        Args:
            plan: Workflow plan to analyze
            
        Returns:
            float: Estimated execution time in seconds
        """
        pass
