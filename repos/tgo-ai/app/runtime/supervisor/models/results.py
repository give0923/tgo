"""
Result consolidation data models.

These models define the structure for consolidating multiple
agent execution results into a unified response.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class ConsolidationStrategy(Enum):
    """Strategies for consolidating multiple agent responses."""
    SYNTHESIS = "synthesis"
    BEST_SELECTION = "best_selection"
    CONSENSUS_BUILDING = "consensus_building"
    CONFLICT_RESOLUTION = "conflict_resolution"
    WEIGHTED_MERGE = "weighted_merge"


@dataclass
class ConflictResolution:
    """Information about conflicts detected and resolved during consolidation."""
    conflict_type: str
    description: str
    resolution_method: str
    affected_agents: List[str]
    confidence_impact: float = 0.0
    
    def __post_init__(self):
        """Validate conflict resolution data."""
        if not self.conflict_type:
            raise ValueError("Conflict type is required")
        if not self.description.strip():
            raise ValueError("Conflict description cannot be empty")
        if not self.resolution_method:
            raise ValueError("Resolution method is required")
        if not self.affected_agents:
            raise ValueError("At least one affected agent must be specified")


@dataclass
class ConsolidationResult:
    """
    Result from consolidating multiple agent execution results.
    
    This represents the final output of the coordination system
    after all agents have been executed and their results merged.
    """
    consolidated_content: str
    consolidation_approach: ConsolidationStrategy
    confidence_score: float
    key_insights: List[str] = field(default_factory=list)
    sources_used: List[str] = field(default_factory=list)
    conflicts_resolved: List[ConflictResolution] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    consolidation_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate consolidation result."""
        if not self.consolidated_content.strip():
            raise ValueError("Consolidated content cannot be empty")
        
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        if self.consolidation_time < 0:
            self.consolidation_time = 0.0
    
    @property
    def has_conflicts(self) -> bool:
        """Check if any conflicts were detected during consolidation."""
        return len(self.conflicts_resolved) > 0
    
    @property
    def consensus_achieved(self) -> bool:
        """Check if consensus was achieved (no unresolved conflicts)."""
        return not self.has_conflicts
    
    @property
    def total_sources(self) -> int:
        """Get total number of sources used in consolidation."""
        return len(self.sources_used)
    
    def add_conflict(self, conflict: ConflictResolution) -> None:
        """Add a conflict resolution to the result."""
        self.conflicts_resolved.append(conflict)
        # Adjust confidence score based on conflict impact
        self.confidence_score = max(0.0, self.confidence_score - conflict.confidence_impact)
    
    def add_insight(self, insight: str) -> None:
        """Add a key insight to the result."""
        if insight.strip() and insight not in self.key_insights:
            self.key_insights.append(insight)
    
    def add_limitation(self, limitation: str) -> None:
        """Add a limitation to the result."""
        if limitation.strip() and limitation not in self.limitations:
            self.limitations.append(limitation)


@dataclass
class ConsolidationRequest:
    """Request for result consolidation."""
    user_message: str
    execution_results: List[Dict[str, Any]]
    consolidation_strategy: Optional[ConsolidationStrategy] = None
    require_consensus: bool = False
    confidence_threshold: float = 0.7
    max_response_length: int = 2000
    enable_memory: bool = False
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate consolidation request."""
        if not self.user_message.strip():
            raise ValueError("User message cannot be empty")
        
        if not self.execution_results:
            raise ValueError("At least one execution result is required")
        
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        
        if self.max_response_length <= 0:
            raise ValueError("Max response length must be positive")


@dataclass
class ConsolidationMetrics:
    """Metrics for consolidation performance and quality."""
    total_results: int
    successful_results: int
    failed_results: int
    consolidation_time: float
    conflicts_detected: int
    conflicts_resolved: int
    consensus_achieved: bool
    final_confidence: float
    strategy_used: ConsolidationStrategy
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of input results."""
        if self.total_results == 0:
            return 0.0
        return self.successful_results / self.total_results
    
    @property
    def conflict_resolution_rate(self) -> float:
        """Calculate conflict resolution rate."""
        if self.conflicts_detected == 0:
            return 1.0
        return self.conflicts_resolved / self.conflicts_detected
