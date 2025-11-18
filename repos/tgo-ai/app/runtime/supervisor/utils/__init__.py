"""
Utility modules for coordination system v2.

This package provides shared utilities for validation,
logging, metrics, and other common functionality.
"""

from .validation import (
    validate_query_analysis_result,
    validate_workflow_plan,
    validate_execution_results,
    validate_consolidation_result
)
from .prompts import (
    build_query_analysis_prompt,
    build_consolidation_prompt,
    format_agent_profiles
)
from .logging import (
    get_coordination_logger,
    log_coordination_metrics,
    create_correlation_id
)
from .metrics import (
    CoordinationMetrics,
    track_execution_time,
    track_success_rate
)

__all__ = [
    # Validation utilities
    "validate_query_analysis_result",
    "validate_workflow_plan",
    "validate_execution_results", 
    "validate_consolidation_result",
    
    # Prompt utilities
    "build_query_analysis_prompt",
    "build_consolidation_prompt",
    "format_agent_profiles",
    
    # Logging utilities
    "get_coordination_logger",
    "log_coordination_metrics",
    "create_correlation_id",
    
    # Metrics utilities
    "CoordinationMetrics",
    "track_execution_time",
    "track_success_rate"
]
