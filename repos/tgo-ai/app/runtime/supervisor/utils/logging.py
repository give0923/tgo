"""
Logging utilities for coordination system v2.

This module provides enhanced logging capabilities with
correlation IDs, structured logging, and metrics tracking.
"""

import uuid
import time
from typing import Dict, Any, Optional
from contextvars import ContextVar

from app.core.logging import get_logger

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def create_correlation_id() -> str:
    """
    Create a new correlation ID for tracking requests.
    
    Returns:
        str: New correlation ID
    """
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID in context.
    
    Args:
        correlation_id: Correlation ID to set
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID from context.
    
    Returns:
        Optional correlation ID
    """
    return correlation_id_var.get()


def get_coordination_logger(component: str) -> Any:
    """
    Get logger with coordination-specific configuration.
    
    Args:
        component: Component name for logging context
        
    Returns:
        Configured logger instance
    """
    logger = get_logger(__name__)
    
    # Add correlation ID if available
    correlation_id = get_correlation_id()
    if correlation_id:
        logger = logger.bind(correlation_id=correlation_id)
    
    return logger.bind(component=f"coordination_v2.{component}")


def log_coordination_metrics(
    logger: Any,
    operation: str,
    duration: float,
    success: bool,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log coordination operation metrics.
    
    Args:
        logger: Logger instance
        operation: Operation name
        duration: Operation duration in seconds
        success: Whether operation succeeded
        metadata: Additional metadata to log
    """
    log_data = {
        "operation": operation,
        "duration": duration,
        "success": success,
        "timestamp": time.time()
    }
    
    if metadata:
        log_data.update(metadata)
    
    if success:
        logger.info(f"Coordination operation completed: {operation}", **log_data)
    else:
        logger.error(f"Coordination operation failed: {operation}", **log_data)


class CoordinationLogContext:
    """
    Context manager for coordination logging with correlation ID.
    
    This ensures all logs within the context have the same correlation ID
    and provides automatic cleanup.
    """
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or create_correlation_id()
        self.previous_correlation_id = None
    
    def __enter__(self) -> str:
        """Enter context and set correlation ID."""
        self.previous_correlation_id = get_correlation_id()
        set_correlation_id(self.correlation_id)
        return self.correlation_id
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context and restore previous correlation ID."""
        set_correlation_id(self.previous_correlation_id)


class OperationTimer:
    """
    Context manager for timing operations with automatic logging.
    """
    
    def __init__(
        self,
        logger: Any,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.logger = logger
        self.operation = operation
        self.metadata = metadata or {}
        self.start_time = None
        self.success = True
    
    def __enter__(self) -> 'OperationTimer':
        """Start timing the operation."""
        self.start_time = time.time()
        self.logger.debug(f"Starting operation: {self.operation}", **self.metadata)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End timing and log results."""
        if self.start_time is None:
            return
        
        duration = time.time() - self.start_time
        self.success = exc_type is None
        
        log_coordination_metrics(
            self.logger,
            self.operation,
            duration,
            self.success,
            self.metadata
        )
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the operation."""
        self.metadata[key] = value
    
    def mark_failure(self) -> None:
        """Mark the operation as failed."""
        self.success = False


def log_query_analysis_start(
    logger: Any,
    user_message: str,
    team_id: str,
    agent_count: int
) -> None:
    """Log the start of query analysis."""
    logger.info(
        "Starting query analysis",
        user_message_length=len(user_message),
        team_id=team_id,
        available_agents=agent_count,
        operation="query_analysis"
    )


def log_query_analysis_complete(
    logger: Any,
    duration: float,
    selected_agents: int,
    workflow_pattern: str,
    confidence_score: float,
    is_complex: bool
) -> None:
    """Log the completion of query analysis."""
    logger.info(
        "Query analysis completed",
        duration=duration,
        selected_agents=selected_agents,
        workflow_pattern=workflow_pattern,
        confidence_score=confidence_score,
        is_complex=is_complex,
        operation="query_analysis"
    )


def log_execution_start(
    logger: Any,
    workflow_pattern: str,
    agent_count: int,
    estimated_time: float
) -> None:
    """Log the start of workflow execution."""
    logger.info(
        "Starting workflow execution",
        workflow_pattern=workflow_pattern,
        agent_count=agent_count,
        estimated_time=estimated_time,
        operation="workflow_execution"
    )


def log_execution_complete(
    logger: Any,
    duration: float,
    successful_agents: int,
    failed_agents: int,
    total_agents: int
) -> None:
    """Log the completion of workflow execution."""
    success_rate = successful_agents / total_agents if total_agents > 0 else 0.0
    
    logger.info(
        "Workflow execution completed",
        duration=duration,
        successful_agents=successful_agents,
        failed_agents=failed_agents,
        total_agents=total_agents,
        success_rate=success_rate,
        operation="workflow_execution"
    )


def log_consolidation_start(
    logger: Any,
    result_count: int,
    successful_results: int
) -> None:
    """Log the start of result consolidation."""
    logger.info(
        "Starting result consolidation",
        result_count=result_count,
        successful_results=successful_results,
        operation="result_consolidation"
    )


def log_consolidation_complete(
    logger: Any,
    duration: float,
    confidence_score: float,
    conflicts_resolved: int,
    strategy_used: str
) -> None:
    """Log the completion of result consolidation."""
    logger.info(
        "Result consolidation completed",
        duration=duration,
        confidence_score=confidence_score,
        conflicts_resolved=conflicts_resolved,
        strategy_used=strategy_used,
        operation="result_consolidation"
    )
