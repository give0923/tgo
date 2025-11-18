"""
Interface for execution management component.

This interface defines the contract for executing workflow plans
and managing multi-agent coordination patterns.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, AsyncIterator

from ..models.execution import WorkflowPlan, ExecutionResult, ExecutionStatus, AgentExecution


class IExecutionManager(ABC):
    """
    Interface for workflow execution and agent coordination.
    
    This component is responsible for:
    1. Executing workflow plans with different patterns
    2. Managing agent lifecycle and status
    3. Handling timeouts, retries, and error recovery
    4. Coordinating parallel, sequential, and hierarchical execution
    5. Collecting and aggregating execution results
    """
    
    @abstractmethod
    async def execute_workflow(
        self,
        workflow_plan: WorkflowPlan,
        auth_headers: Dict[str, str]
    ) -> List[ExecutionResult]:
        """
        Execute complete workflow plan and return results.
        
        This method:
        - Executes agents according to the workflow pattern
        - Handles dependencies and execution order
        - Manages timeouts and error recovery
        - Collects results from all agent executions
        
        Args:
            workflow_plan: Plan to execute
            auth_headers: Authentication headers for agent service calls
            
        Returns:
            List[ExecutionResult]: Results from all agent executions
            
        Raises:
            ExecutionError: When execution fails
            TimeoutError: When execution exceeds timeout
            AuthenticationError: When authentication fails
        """
        pass
    
    @abstractmethod
    async def execute_parallel(
        self,
        executions: List[AgentExecution],
        auth_headers: Dict[str, str],
        timeout: Optional[int] = None
    ) -> List[ExecutionResult]:
        """
        Execute multiple agents in parallel.
        
        Args:
            executions: Agent executions to run in parallel
            auth_headers: Authentication headers
            timeout: Optional timeout override
            
        Returns:
            List[ExecutionResult]: Results from parallel execution
            
        Raises:
            ExecutionError: When parallel execution fails
        """
        pass
    
    @abstractmethod
    async def execute_sequential(
        self,
        executions: List[AgentExecution],
        auth_headers: Dict[str, str],
        timeout: Optional[int] = None
    ) -> List[ExecutionResult]:
        """
        Execute agents sequentially with result chaining.
        
        Args:
            executions: Agent executions to run sequentially
            auth_headers: Authentication headers
            timeout: Optional timeout override
            
        Returns:
            List[ExecutionResult]: Results from sequential execution
            
        Raises:
            ExecutionError: When sequential execution fails
        """
        pass
    
    @abstractmethod
    async def execute_hierarchical(
        self,
        executions: List[AgentExecution],
        auth_headers: Dict[str, str],
        hierarchy_levels: List[List[str]],
        timeout: Optional[int] = None
    ) -> List[ExecutionResult]:
        """
        Execute agents in hierarchical pattern.
        
        Args:
            executions: Agent executions to coordinate
            auth_headers: Authentication headers
            hierarchy_levels: Levels of hierarchy (agent IDs per level)
            timeout: Optional timeout override
            
        Returns:
            List[ExecutionResult]: Results from hierarchical execution
            
        Raises:
            ExecutionError: When hierarchical execution fails
        """
        pass
    
    @abstractmethod
    async def monitor_execution_progress(
        self,
        workflow_plan: WorkflowPlan
    ) -> AsyncIterator[Dict[str, ExecutionStatus]]:
        """
        Monitor execution progress in real-time.
        
        Args:
            workflow_plan: Plan being executed
            
        Yields:
            Dict mapping agent IDs to their current execution status
        """
        pass
    
    @abstractmethod
    async def cancel_execution(
        self,
        workflow_plan: WorkflowPlan
    ) -> bool:
        """
        Cancel ongoing workflow execution.
        
        Args:
            workflow_plan: Plan to cancel
            
        Returns:
            bool: True if cancellation was successful
        """
        pass
