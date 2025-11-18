"""
Execution-related data models.

These models define the structure for workflow planning,
execution patterns, and agent execution results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid

from app.models.internal import Agent, CoordinationContext


class WorkflowPattern(Enum):
    """Execution patterns for multi-agent coordination."""
    SINGLE = "single"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"
    PIPELINE = "pipeline"


class ExecutionStatus(Enum):
    """Status of agent execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class AgentExecution:
    """Represents the execution of a single agent."""
    agent_id: str
    agent_name: str
    sub_question_id: Optional[str]
    question: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    
    def __post_init__(self):
        """Validate agent execution data."""
        if not self.agent_id:
            raise ValueError("Agent ID is required")
        if not self.agent_name:
            raise ValueError("Agent name is required")
        if not self.question.strip():
            raise ValueError("Question cannot be empty")
    
    @property
    def is_completed(self) -> bool:
        """Check if execution is completed (successfully or not)."""
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, 
                              ExecutionStatus.TIMEOUT, ExecutionStatus.CANCELLED]
    
    @property
    def is_successful(self) -> bool:
        """Check if execution completed successfully."""
        return self.status == ExecutionStatus.COMPLETED


@dataclass
class ExecutionResult:
    """Result from executing an agent."""
    execution_id: str
    agent_id: str
    agent_name: str
    sub_question_id: Optional[str]
    question: str
    response: str
    success: bool
    execution_time: float
    start_time: datetime
    end_time: datetime
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate execution result."""
        if not self.execution_id:
            raise ValueError("Execution ID is required")
        if not self.agent_id:
            raise ValueError("Agent ID is required")
        if not self.agent_name:
            raise ValueError("Agent name is required")
        if not self.question.strip():
            raise ValueError("Question cannot be empty")
        if self.success and not self.response.strip():
            raise ValueError("Successful execution must have a response")
        if not self.success and not self.error:
            raise ValueError("Failed execution must have an error message")


@dataclass
class WorkflowPlan:
    """Executable workflow plan created from query analysis."""
    plan_id: str
    pattern: WorkflowPattern
    agent_executions: List[AgentExecution]
    context: CoordinationContext
    dependencies: List[str] = field(default_factory=list)
    parallel_groups: List[List[str]] = field(default_factory=list)
    estimated_time: float = 30.0
    timeout: int = 300
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate workflow plan."""
        if not self.plan_id:
            self.plan_id = str(uuid.uuid4())
        
        if not self.agent_executions:
            raise ValueError("Workflow plan must have at least one agent execution")
        
        if self.estimated_time <= 0:
            self.estimated_time = 30.0
            
        if self.timeout <= 0:
            self.timeout = 300
        
        # Validate that all agent IDs in parallel groups exist in executions
        execution_agent_ids = {exec.agent_id for exec in self.agent_executions}
        for group in self.parallel_groups:
            for agent_id in group:
                if agent_id not in execution_agent_ids:
                    raise ValueError(f"Agent ID {agent_id} in parallel group not found in executions")
    
    @property
    def total_agents(self) -> int:
        """Get total number of agents in the plan."""
        return len(self.agent_executions)
    
    def get_execution_by_agent_id(self, agent_id: str) -> Optional[AgentExecution]:
        """Get agent execution by agent ID."""
        for execution in self.agent_executions:
            if execution.agent_id == agent_id:
                return execution
        return None
    
    def get_executions_by_status(self, status: ExecutionStatus) -> List[AgentExecution]:
        """Get all executions with a specific status."""
        return [exec for exec in self.agent_executions if exec.status == status]
