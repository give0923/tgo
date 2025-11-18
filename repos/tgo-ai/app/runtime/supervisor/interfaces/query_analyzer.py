"""
Interface for query analysis component.

This interface defines the contract for LLM-powered query decomposition
and agent assignment functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict

from app.models.internal import CoordinationContext
from ..models.coordination import QueryAnalysisResult


class IQueryAnalyzer(ABC):
    """
    Interface for query analysis and agent assignment.
    
    This component is responsible for:
    1. Analyzing user queries using LLM
    2. Decomposing complex queries into sub-questions
    3. Assigning sub-questions to appropriate agents
    4. Determining optimal workflow patterns
    5. Creating execution plans with dependencies
    """
    
    @abstractmethod
    async def analyze_query(
        self,
        context: CoordinationContext,
        auth_headers: Dict[str, str]
    ) -> QueryAnalysisResult:
        """
        Analyze user query and create coordination plan.
        
        This method uses LLM to:
        - Understand user intent and complexity
        - Decompose multi-intent queries into sub-questions
        - Select appropriate agents based on capabilities
        - Determine optimal workflow execution pattern
        - Create execution plan with dependencies and timing
        
        Args:
            context: Coordination context with user message and team info
            auth_headers: Authentication headers for LLM service calls
            
        Returns:
            QueryAnalysisResult: Complete analysis with agent assignments
            
        Raises:
            QueryAnalysisError: When LLM analysis fails
            ValidationError: When input validation fails
            AuthenticationError: When authentication fails
        """
        pass
    
    @abstractmethod
    async def validate_analysis_result(
        self,
        result: QueryAnalysisResult,
        context: CoordinationContext
    ) -> bool:
        """
        Validate the analysis result for consistency and feasibility.
        
        Args:
            result: Query analysis result to validate
            context: Original coordination context
            
        Returns:
            bool: True if result is valid and feasible
            
        Raises:
            ValidationError: When validation fails
        """
        pass
    
    @abstractmethod
    def get_supported_workflow_patterns(self) -> list[str]:
        """
        Get list of supported workflow patterns.
        
        Returns:
            List of supported workflow pattern names
        """
        pass
