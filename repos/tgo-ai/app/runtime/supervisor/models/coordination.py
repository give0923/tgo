"""
Core coordination data models.

These models define the structure for coordination requests, responses,
and the LLM-generated query analysis results that match the exact
JSON format specified in the requirements.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid
from datetime import datetime

from app.models.internal import Team, CoordinationContext
from .execution import ExecutionResult


class WorkflowType(Enum):
    """Supported workflow execution patterns."""
    SINGLE = "single"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"
    PIPELINE = "pipeline"


@dataclass
class SubQuestion:
    """
    Represents a decomposed sub-question assigned to a specific agent.
    
    This matches the exact format required by the LLM response specification.
    """
    id: str
    question: str
    assigned_agent_id: str
    
    def __post_init__(self):
        """Validate sub-question data."""
        if not self.id or not self.id.startswith("sq_"):
            raise ValueError("Sub-question ID must start with 'sq_'")
        if not self.question.strip():
            raise ValueError("Sub-question cannot be empty")
        if not self.assigned_agent_id:
            raise ValueError("Sub-question must have an assigned agent ID")


@dataclass
class ExecutionPlan:
    """
    Execution plan with dependencies and parallel groups.
    
    This matches the exact format required by the LLM response specification.
    """
    dependencies: List[str] = field(default_factory=list)
    parallel_groups: List[List[str]] = field(default_factory=list)
    estimated_time: float = 30.0
    
    def __post_init__(self):
        """Validate execution plan data."""
        if self.estimated_time <= 0:
            self.estimated_time = 30.0
        
        # Validate parallel groups contain valid agent IDs
        for group in self.parallel_groups:
            if not isinstance(group, list) or not group:
                raise ValueError("Each parallel group must be a non-empty list")


@dataclass
class QueryAnalysisResult:
    """
    Result from LLM-powered query analysis and agent assignment.
    
    This matches the EXACT JSON format specified in the requirements:
    {
      "selected_agent_ids": ["99010ace-aa82-46a1-bdb4-04254fa55b6f"],
      "selection_reasoning": "...",
      "workflow": "parallel",
      "workflow_reasoning": "...",
      "confidence_score": 0.9,
      "is_complex": true,
      "sub_questions": [...],
      "execution_plan": {...}
    }
    """
    selected_agent_ids: List[str]
    selection_reasoning: str
    workflow: str  # Will be converted to WorkflowType enum
    workflow_reasoning: str
    confidence_score: float
    is_complex: bool
    sub_questions: List[SubQuestion] = field(default_factory=list)
    execution_plan: ExecutionPlan = field(default_factory=ExecutionPlan)
    
    def __post_init__(self):
        """Validate and normalize query analysis result."""
        # Validate required fields
        if not self.selected_agent_ids:
            raise ValueError("At least one agent must be selected")
        
        if not self.selection_reasoning.strip():
            raise ValueError("Selection reasoning cannot be empty")
            
        if not self.workflow_reasoning.strip():
            raise ValueError("Workflow reasoning cannot be empty")
            
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        # Validate workflow type
        try:
            WorkflowType(self.workflow)
        except ValueError:
            valid_workflows = [w.value for w in WorkflowType]
            raise ValueError(f"Invalid workflow '{self.workflow}'. Must be one of: {valid_workflows}")
        
        # Ensure sub_questions and execution_plan are properly initialized
        if self.sub_questions is None:
            self.sub_questions = []
        if self.execution_plan is None:
            self.execution_plan = ExecutionPlan()
    
    @property
    def workflow_type(self) -> WorkflowType:
        """Get workflow as enum type."""
        return WorkflowType(self.workflow)


@dataclass
class CoordinationRequest:
    """Request for coordination services."""
    context: CoordinationContext
    auth_headers: Dict[str, str]
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate coordination request."""
        if not self.context:
            raise ValueError("Coordination context is required")
        if not self.auth_headers:
            raise ValueError("Authentication headers are required")


@dataclass
class CoordinationResponse:
    """Response from coordination services."""
    success: bool
    request_id: str
    message: str
    consolidated_response: str
    execution_results: List[ExecutionResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate coordination response."""
        if not self.request_id:
            raise ValueError("Request ID is required")
        if not self.message:
            raise ValueError("Response message is required")
        if self.success and not self.consolidated_response:
            raise ValueError("Successful response must have consolidated content")
