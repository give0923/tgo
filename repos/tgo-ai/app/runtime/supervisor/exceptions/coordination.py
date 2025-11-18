"""
Comprehensive exception hierarchy for coordination system v2.

This module provides specific exception types for different coordination
failures, enabling precise error handling and debugging.
"""

from typing import Optional, Dict, Any, List


class CoordinationError(Exception):
    """Base exception for all coordination-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "error_code": self.error_code,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None
        }


class QueryAnalysisError(CoordinationError):
    """Raised when LLM-powered query analysis fails."""
    
    def __init__(
        self,
        message: str,
        user_query: Optional[str] = None,
        model_name: Optional[str] = None,
        prompt_length: Optional[int] = None,
        response_length: Optional[int] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        self.user_query = user_query
        self.model_name = model_name
        self.prompt_length = prompt_length
        self.response_length = response_length


class WorkflowPlanningError(CoordinationError):
    """Raised when workflow planning fails."""
    
    def __init__(
        self,
        message: str,
        workflow_pattern: Optional[str] = None,
        agent_count: Optional[int] = None,
        dependency_errors: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        self.workflow_pattern = workflow_pattern
        self.agent_count = agent_count
        self.dependency_errors = dependency_errors or []


class ExecutionError(CoordinationError):
    """Raised when agent execution fails."""
    
    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        execution_pattern: Optional[str] = None,
        failed_agents: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.execution_pattern = execution_pattern
        self.failed_agents = failed_agents or []


class ConsolidationError(CoordinationError):
    """Raised when result consolidation fails."""
    
    def __init__(
        self,
        message: str,
        result_count: Optional[int] = None,
        consolidation_strategy: Optional[str] = None,
        conflicts_detected: Optional[int] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        self.result_count = result_count
        self.consolidation_strategy = consolidation_strategy
        self.conflicts_detected = conflicts_detected


class ValidationError(CoordinationError):
    """Raised when input validation fails."""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        validation_rule: Optional[str] = None,
        validation_errors: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        self.field_name = field_name
        self.field_value = field_value
        self.validation_rule = validation_rule
        self.validation_errors = validation_errors or []


class ConfigurationError(CoordinationError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_value: Optional[Any] = None,
        required_keys: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        self.config_key = config_key
        self.config_value = config_value
        self.required_keys = required_keys or []


class TimeoutError(CoordinationError):
    """Raised when operations exceed timeout limits."""
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation_type: Optional[str] = None,
        elapsed_time: Optional[float] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        self.timeout_seconds = timeout_seconds
        self.operation_type = operation_type
        self.elapsed_time = elapsed_time


class AuthenticationError(CoordinationError):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        auth_method: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        self.service_name = service_name
        self.auth_method = auth_method


class LLMResponseError(QueryAnalysisError):
    """Raised when LLM response is invalid or unparseable."""
    
    def __init__(
        self,
        message: str,
        raw_response: Optional[str] = None,
        expected_format: Optional[str] = None,
        parsing_errors: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        self.raw_response = raw_response
        self.expected_format = expected_format
        self.parsing_errors = parsing_errors or []


class AgentNotFoundError(ExecutionError):
    """Raised when a required agent is not found or available."""
    
    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        available_agents: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        super().__init__(message, agent_id=agent_id, **kwargs)
        self.available_agents = available_agents or []


class DependencyError(WorkflowPlanningError):
    """Raised when workflow dependencies cannot be resolved."""
    
    def __init__(
        self,
        message: str,
        circular_dependencies: Optional[List[str]] = None,
        missing_dependencies: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        super().__init__(message, **kwargs)
        self.circular_dependencies = circular_dependencies or []
        self.missing_dependencies = missing_dependencies or []
