"""
Exception classes for the coordination system v2.

This module provides a comprehensive hierarchy of exceptions
for different types of coordination failures.
"""

from .coordination import (
    CoordinationError,
    QueryAnalysisError,
    WorkflowPlanningError,
    ExecutionError,
    ConsolidationError,
    ValidationError,
    ConfigurationError,
    TimeoutError,
    AuthenticationError
)

__all__ = [
    "CoordinationError",
    "QueryAnalysisError", 
    "WorkflowPlanningError",
    "ExecutionError",
    "ConsolidationError",
    "ValidationError",
    "ConfigurationError",
    "TimeoutError",
    "AuthenticationError"
]
