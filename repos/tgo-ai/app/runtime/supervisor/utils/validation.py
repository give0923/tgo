"""
Validation utilities for coordination system v2.

This module provides comprehensive validation functions for all
coordination data models and business logic constraints.
"""

from typing import List, Dict, Any, Set
import uuid

from app.models.internal import CoordinationContext, Agent

from ..models.coordination import QueryAnalysisResult, WorkflowType
from ..models.execution import WorkflowPlan, ExecutionResult, WorkflowPattern
from ..models.results import ConsolidationResult


def validate_query_analysis_result(
    result: QueryAnalysisResult,
    context: CoordinationContext
) -> List[str]:
    """
    Validate query analysis result for consistency and feasibility.
    
    Args:
        result: Query analysis result to validate
        context: Original coordination context
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Validate basic structure
    if not result.selected_agent_ids:
        errors.append("At least one agent must be selected")
    
    if not result.selection_reasoning.strip():
        errors.append("Selection reasoning cannot be empty")
    
    if not result.workflow_reasoning.strip():
        errors.append("Workflow reasoning cannot be empty")
    
    # Validate confidence score
    if not 0.0 <= result.confidence_score <= 1.0:
        errors.append(f"Confidence score {result.confidence_score} must be between 0.0 and 1.0")
    
    # Validate workflow type
    try:
        WorkflowType(result.workflow)
    except ValueError:
        valid_workflows = [w.value for w in WorkflowType]
        errors.append(f"Invalid workflow '{result.workflow}'. Must be one of: {valid_workflows}")
    
    # Validate agent selection against available agents
    available_agent_ids = {str(agent.id) for agent in context.team.agents}
    for agent_id in result.selected_agent_ids:
        if agent_id not in available_agent_ids:
            errors.append(f"Selected agent {agent_id} not found in available agents")
    
    # Validate agent count constraints
    if len(result.selected_agent_ids) > context.max_agents:
        errors.append(f"Selected {len(result.selected_agent_ids)} agents exceeds maximum {context.max_agents}")
    
    # Validate sub-questions consistency
    if result.is_complex:
        if not result.sub_questions:
            errors.append("Complex queries must have sub-questions")
        
        # Check sub-question agent assignments
        sub_question_agents = {sq.assigned_agent_id for sq in result.sub_questions}
        selected_agents_set = set(result.selected_agent_ids)
        
        if sub_question_agents != selected_agents_set:
            errors.append("Sub-question agent assignments must match selected agents")
        
        # Validate sub-question IDs
        sub_question_ids = [sq.id for sq in result.sub_questions]
        if len(sub_question_ids) != len(set(sub_question_ids)):
            errors.append("Sub-question IDs must be unique")
        
        for sq in result.sub_questions:
            if not sq.id.startswith("sq_"):
                errors.append(f"Sub-question ID '{sq.id}' must start with 'sq_'")
            if not sq.question.strip():
                errors.append(f"Sub-question '{sq.id}' cannot have empty question")
    
    # Validate execution plan
    if result.execution_plan:
        if result.execution_plan.estimated_time <= 0:
            errors.append("Execution plan estimated time must be positive")
        
        # Validate parallel groups contain valid agent IDs
        for i, group in enumerate(result.execution_plan.parallel_groups):
            if not group:
                errors.append(f"Parallel group {i} cannot be empty")
            for agent_id in group:
                if agent_id not in result.selected_agent_ids:
                    errors.append(f"Agent {agent_id} in parallel group not in selected agents")
    
    return errors


def validate_workflow_plan(
    plan: WorkflowPlan,
    context: CoordinationContext
) -> List[str]:
    """
    Validate workflow plan for feasibility and consistency.
    
    Args:
        plan: Workflow plan to validate
        context: Coordination context
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Validate basic structure
    if not plan.agent_executions:
        errors.append("Workflow plan must have at least one agent execution")
    
    if plan.estimated_time <= 0:
        errors.append("Estimated time must be positive")
    
    if plan.timeout <= 0:
        errors.append("Timeout must be positive")
    
    # Validate agent executions
    execution_agent_ids = set()
    for execution in plan.agent_executions:
        if execution.agent_id in execution_agent_ids:
            errors.append(f"Duplicate agent execution for agent {execution.agent_id}")
        execution_agent_ids.add(execution.agent_id)
        
        if not execution.question.strip():
            errors.append(f"Agent execution {execution.agent_id} has empty question")
    
    # Validate parallel groups
    for i, group in enumerate(plan.parallel_groups):
        if not group:
            errors.append(f"Parallel group {i} cannot be empty")
        for agent_id in group:
            if agent_id not in execution_agent_ids:
                errors.append(f"Agent {agent_id} in parallel group not found in executions")
    
    # Validate dependencies
    for dependency in plan.dependencies:
        # This is a simplified validation - in practice you'd check for cycles
        if not dependency.strip():
            errors.append("Dependencies cannot be empty strings")
    
    # Validate against context constraints
    if len(plan.agent_executions) > context.max_agents:
        errors.append(f"Plan has {len(plan.agent_executions)} executions, exceeds max {context.max_agents}")
    
    return errors


def validate_execution_results(
    results: List[ExecutionResult],
    expected_agent_ids: Set[str]
) -> List[str]:
    """
    Validate execution results for completeness and consistency.
    
    Args:
        results: Execution results to validate
        expected_agent_ids: Set of expected agent IDs
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if not results:
        errors.append("At least one execution result is required")
        return errors
    
    # Check for expected agents
    result_agent_ids = {result.agent_id for result in results}
    missing_agents = expected_agent_ids - result_agent_ids
    if missing_agents:
        errors.append(f"Missing execution results for agents: {missing_agents}")
    
    extra_agents = result_agent_ids - expected_agent_ids
    if extra_agents:
        errors.append(f"Unexpected execution results for agents: {extra_agents}")
    
    # Validate individual results
    for result in results:
        if not result.execution_id:
            errors.append(f"Execution result for agent {result.agent_id} missing execution ID")
        
        if not result.question.strip():
            errors.append(f"Execution result for agent {result.agent_id} has empty question")
        
        if result.success and not result.response.strip():
            errors.append(f"Successful execution for agent {result.agent_id} has empty response")
        
        if not result.success and not result.error:
            errors.append(f"Failed execution for agent {result.agent_id} missing error message")
        
        if result.execution_time < 0:
            errors.append(f"Execution time for agent {result.agent_id} cannot be negative")
    
    return errors


def validate_consolidation_result(
    result: ConsolidationResult
) -> List[str]:
    """
    Validate consolidation result for completeness and consistency.
    
    Args:
        result: Consolidation result to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Validate basic structure
    if not result.consolidated_content.strip():
        errors.append("Consolidated content cannot be empty")
    
    if not 0.0 <= result.confidence_score <= 1.0:
        errors.append(f"Confidence score {result.confidence_score} must be between 0.0 and 1.0")
    
    if result.consolidation_time < 0:
        errors.append("Consolidation time cannot be negative")
    
    # Validate conflicts
    for i, conflict in enumerate(result.conflicts_resolved):
        if not conflict.conflict_type:
            errors.append(f"Conflict {i} missing conflict type")
        
        if not conflict.description.strip():
            errors.append(f"Conflict {i} has empty description")
        
        if not conflict.affected_agents:
            errors.append(f"Conflict {i} must have at least one affected agent")
    
    # Validate insights and limitations
    for i, insight in enumerate(result.key_insights):
        if not insight.strip():
            errors.append(f"Key insight {i} cannot be empty")
    
    for i, limitation in enumerate(result.limitations):
        if not limitation.strip():
            errors.append(f"Limitation {i} cannot be empty")
    
    return errors


def validate_agent_id(agent_id: str) -> bool:
    """
    Validate agent ID format.
    
    Args:
        agent_id: Agent ID to validate
        
    Returns:
        bool: True if valid UUID format
    """
    try:
        uuid.UUID(agent_id)
        return True
    except ValueError:
        return False


def validate_sub_question_id(sub_question_id: str) -> bool:
    """
    Validate sub-question ID format.
    
    Args:
        sub_question_id: Sub-question ID to validate
        
    Returns:
        bool: True if valid format (starts with 'sq_')
    """
    return sub_question_id.startswith("sq_") and len(sub_question_id) > 3
