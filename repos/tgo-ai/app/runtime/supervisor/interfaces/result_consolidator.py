"""
Interface for result consolidation component.

This interface defines the contract for consolidating multiple
agent execution results into unified responses.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from app.models.internal import CoordinationContext
from ..models.execution import ExecutionResult
from ..models.results import ConsolidationResult, ConsolidationStrategy, ConsolidationRequest


class IResultConsolidator(ABC):
    """
    Interface for result consolidation and response synthesis.
    
    This component is responsible for:
    1. Consolidating multiple agent responses using LLM
    2. Resolving conflicts between different agent outputs
    3. Building consensus from diverse perspectives
    4. Synthesizing coherent unified responses
    5. Maintaining source attribution and confidence scoring
    """
    
    @abstractmethod
    async def consolidate_results(
        self,
        execution_results: List[ExecutionResult],
        context: CoordinationContext,
        strategy: Optional[ConsolidationStrategy] = None
    ) -> ConsolidationResult:
        """
        Consolidate multiple execution results into unified response.
        
        This method:
        - Analyzes all agent responses for consistency
        - Identifies and resolves conflicts
        - Synthesizes information using LLM
        - Maintains source attribution
        - Calculates confidence scores
        
        Args:
            execution_results: Results from agent executions
            context: Original coordination context
            strategy: Optional consolidation strategy override
            
        Returns:
            ConsolidationResult: Unified consolidated response
            
        Raises:
            ConsolidationError: When consolidation fails
            ValidationError: When input validation fails
        """
        pass
    
    @abstractmethod
    async def detect_conflicts(
        self,
        execution_results: List[ExecutionResult]
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts between agent responses.
        
        Args:
            execution_results: Results to analyze for conflicts
            
        Returns:
            List of detected conflicts with details
        """
        pass
    
    @abstractmethod
    async def synthesize_responses(
        self,
        consolidation_request: ConsolidationRequest
    ) -> ConsolidationResult:
        """
        Synthesize responses using advanced LLM techniques.
        
        Args:
            consolidation_request: Detailed consolidation request
            
        Returns:
            ConsolidationResult: Synthesized response
            
        Raises:
            ConsolidationError: When synthesis fails
        """
        pass
    
    @abstractmethod
    def select_consolidation_strategy(
        self,
        execution_results: List[ExecutionResult],
        context: CoordinationContext
    ) -> ConsolidationStrategy:
        """
        Select optimal consolidation strategy based on results.
        
        Args:
            execution_results: Results to analyze
            context: Coordination context
            
        Returns:
            ConsolidationStrategy: Recommended strategy
        """
        pass
    
    @abstractmethod
    def calculate_confidence_score(
        self,
        execution_results: List[ExecutionResult],
        consolidation_result: ConsolidationResult
    ) -> float:
        """
        Calculate confidence score for consolidated result.
        
        Args:
            execution_results: Original execution results
            consolidation_result: Consolidated result
            
        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        pass
