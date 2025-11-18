"""
Metrics tracking utilities for coordination system v2.

This module provides comprehensive metrics collection and
performance tracking for coordination operations.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque
from threading import Lock


@dataclass
class OperationMetrics:
    """Metrics for a single operation."""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, success: bool = True) -> None:
        """Mark operation as complete."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the operation."""
        self.metadata[key] = value


@dataclass
class CoordinationMetrics:
    """Comprehensive metrics for coordination operations."""
    
    # Request-level metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Query analysis metrics
    query_analysis_count: int = 0
    query_analysis_total_time: float = 0.0
    query_analysis_failures: int = 0
    
    # Workflow execution metrics
    workflow_executions: int = 0
    workflow_total_time: float = 0.0
    workflow_failures: int = 0
    
    # Agent execution metrics
    agent_executions: int = 0
    agent_execution_total_time: float = 0.0
    agent_execution_failures: int = 0
    
    # Consolidation metrics
    consolidations: int = 0
    consolidation_total_time: float = 0.0
    consolidation_failures: int = 0
    
    # Pattern usage tracking
    workflow_patterns: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Recent operation times (for calculating moving averages)
    recent_operation_times: Dict[str, deque] = field(default_factory=lambda: defaultdict(lambda: deque(maxlen=100)))
    
    # Thread safety
    _lock: Lock = field(default_factory=Lock, init=False)
    
    def record_request(self, success: bool) -> None:
        """Record a coordination request."""
        with self._lock:
            self.total_requests += 1
            if success:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
    
    def record_query_analysis(self, duration: float, success: bool) -> None:
        """Record query analysis metrics."""
        with self._lock:
            self.query_analysis_count += 1
            self.query_analysis_total_time += duration
            if not success:
                self.query_analysis_failures += 1
            self.recent_operation_times['query_analysis'].append(duration)
    
    def record_workflow_execution(self, duration: float, success: bool, pattern: str) -> None:
        """Record workflow execution metrics."""
        with self._lock:
            self.workflow_executions += 1
            self.workflow_total_time += duration
            if not success:
                self.workflow_failures += 1
            self.workflow_patterns[pattern] += 1
            self.recent_operation_times['workflow_execution'].append(duration)
    
    def record_agent_execution(self, duration: float, success: bool) -> None:
        """Record agent execution metrics."""
        with self._lock:
            self.agent_executions += 1
            self.agent_execution_total_time += duration
            if not success:
                self.agent_execution_failures += 1
            self.recent_operation_times['agent_execution'].append(duration)
    
    def record_consolidation(self, duration: float, success: bool) -> None:
        """Record consolidation metrics."""
        with self._lock:
            self.consolidations += 1
            self.consolidation_total_time += duration
            if not success:
                self.consolidation_failures += 1
            self.recent_operation_times['consolidation'].append(duration)
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests
    
    @property
    def query_analysis_avg_time(self) -> float:
        """Calculate average query analysis time."""
        if self.query_analysis_count == 0:
            return 0.0
        return self.query_analysis_total_time / self.query_analysis_count
    
    @property
    def workflow_execution_avg_time(self) -> float:
        """Calculate average workflow execution time."""
        if self.workflow_executions == 0:
            return 0.0
        return self.workflow_total_time / self.workflow_executions
    
    @property
    def consolidation_avg_time(self) -> float:
        """Calculate average consolidation time."""
        if self.consolidations == 0:
            return 0.0
        return self.consolidation_total_time / self.consolidations
    
    def get_recent_avg_time(self, operation: str) -> float:
        """Get recent average time for an operation."""
        with self._lock:
            times = self.recent_operation_times.get(operation, deque())
            if not times:
                return 0.0
            return sum(times) / len(times)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        with self._lock:
            return {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate": self.success_rate,
                "query_analysis": {
                    "count": self.query_analysis_count,
                    "total_time": self.query_analysis_total_time,
                    "avg_time": self.query_analysis_avg_time,
                    "failures": self.query_analysis_failures,
                    "recent_avg_time": self.get_recent_avg_time('query_analysis')
                },
                "workflow_execution": {
                    "count": self.workflow_executions,
                    "total_time": self.workflow_total_time,
                    "avg_time": self.workflow_execution_avg_time,
                    "failures": self.workflow_failures,
                    "recent_avg_time": self.get_recent_avg_time('workflow_execution')
                },
                "agent_execution": {
                    "count": self.agent_executions,
                    "total_time": self.agent_execution_total_time,
                    "avg_time": self.agent_execution_total_time / max(1, self.agent_executions),
                    "failures": self.agent_execution_failures,
                    "recent_avg_time": self.get_recent_avg_time('agent_execution')
                },
                "consolidation": {
                    "count": self.consolidations,
                    "total_time": self.consolidation_total_time,
                    "avg_time": self.consolidation_avg_time,
                    "failures": self.consolidation_failures,
                    "recent_avg_time": self.get_recent_avg_time('consolidation')
                },
                "workflow_patterns": dict(self.workflow_patterns)
            }


# Global metrics instance
_global_metrics = CoordinationMetrics()


def get_global_metrics() -> CoordinationMetrics:
    """Get the global metrics instance."""
    return _global_metrics


def track_execution_time(operation: str):
    """
    Decorator to track execution time of functions.
    
    Args:
        operation: Operation name for metrics
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                duration = time.time() - start_time
                
                # Record metrics based on operation type
                if operation == "query_analysis":
                    _global_metrics.record_query_analysis(duration, success)
                elif operation == "workflow_execution":
                    pattern = kwargs.get('pattern', 'unknown')
                    _global_metrics.record_workflow_execution(duration, success, pattern)
                elif operation == "agent_execution":
                    _global_metrics.record_agent_execution(duration, success)
                elif operation == "consolidation":
                    _global_metrics.record_consolidation(duration, success)
        
        return wrapper
    return decorator


def track_success_rate(operation: str):
    """
    Decorator to track success rate of operations.
    
    Args:
        operation: Operation name for metrics
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                _global_metrics.record_request(True)
                return result
            except Exception as e:
                _global_metrics.record_request(False)
                raise
        
        return wrapper
    return decorator


class MetricsCollector:
    """Context manager for collecting detailed operation metrics."""
    
    def __init__(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None):
        self.operation_name = operation_name
        self.metadata = metadata or {}
        self.metrics = OperationMetrics(operation_name, time.time(), metadata=self.metadata)
    
    def __enter__(self) -> OperationMetrics:
        """Start collecting metrics."""
        return self.metrics
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Complete metrics collection."""
        success = exc_type is None
        self.metrics.complete(success)
        
        # Record in global metrics
        duration = self.metrics.duration or 0.0
        if self.operation_name == "query_analysis":
            _global_metrics.record_query_analysis(duration, success)
        elif self.operation_name == "workflow_execution":
            pattern = self.metadata.get('pattern', 'unknown')
            _global_metrics.record_workflow_execution(duration, success, pattern)
        elif self.operation_name == "agent_execution":
            _global_metrics.record_agent_execution(duration, success)
        elif self.operation_name == "consolidation":
            _global_metrics.record_consolidation(duration, success)
