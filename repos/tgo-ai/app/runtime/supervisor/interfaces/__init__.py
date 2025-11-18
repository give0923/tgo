"""
Interfaces for the coordination system v2.

This module defines the contracts for all major components,
enabling dependency injection, testing, and modularity.
"""

from .query_analyzer import IQueryAnalyzer
from .workflow_planner import IWorkflowPlanner
from .execution_manager import IExecutionManager
from .result_consolidator import IResultConsolidator

__all__ = [
    "IQueryAnalyzer",
    "IWorkflowPlanner", 
    "IExecutionManager",
    "IResultConsolidator"
]
