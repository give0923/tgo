"""
Data models for the coordination system v2.

This module provides type-safe data models that ensure consistency
and validation throughout the coordination workflow.
"""

from .coordination import (
    CoordinationRequest,
    CoordinationResponse,
    QueryAnalysisResult,
    SubQuestion,
    ExecutionPlan
)
from .execution import (
    WorkflowPattern,
    WorkflowPlan,
    ExecutionResult,
    AgentExecution
)
from .results import (
    ConsolidationResult,
    ConsolidationStrategy,
    ConflictResolution
)

__all__ = [
    # Coordination models
    "CoordinationRequest",
    "CoordinationResponse", 
    "QueryAnalysisResult",
    "SubQuestion",
    "ExecutionPlan",
    
    # Execution models
    "WorkflowPattern",
    "WorkflowPlan",
    "ExecutionResult",
    "AgentExecution",
    
    # Result models
    "ConsolidationResult",
    "ConsolidationStrategy",
    "ConflictResolution"
]
