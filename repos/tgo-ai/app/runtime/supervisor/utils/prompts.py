"""
Prompt building utilities for coordination system v2.

This module provides functions for building structured prompts
for LLM interactions in query analysis and result consolidation.
"""

from typing import List, Dict, Any
from app.models.internal import CoordinationContext, Agent
from ..configuration.settings import QueryAnalysisConfig, ConsolidationConfig
from ..models.execution import ExecutionResult


def build_query_analysis_prompt(
    context: CoordinationContext,
    config: QueryAnalysisConfig
) -> str:
    """
    Build comprehensive query analysis prompt for LLM.
    
    This creates the exact prompt structure needed to get the
    required JSON response format from the LLM.
    """
    agent_profiles = format_agent_profiles(context.team.agents)
    
    prompt = f"""You are an expert AI coordination system responsible for intelligent agent selection, task decomposition, and workflow orchestration. Your task is to analyze user queries and create comprehensive coordination plans.

USER MESSAGE:
"{context.message}"

TEAM CONTEXT:
Team Name: {context.team.name}
Team Description: {context.team.instruction or "General purpose team"}
Session ID: {context.session_id or "default"}

COORDINATION REQUIREMENTS:
Maximum Agents: {context.max_agents}
Require Consensus: {context.require_consensus}
Timeout: {context.timeout} seconds

AVAILABLE AGENTS:
{agent_profiles}

ANALYSIS INSTRUCTIONS:
1. **Intent Analysis**: Carefully analyze the user's message to understand:
   - Primary intent and goals
   - Complexity level (simple single-intent vs complex multi-intent)
   - Required expertise domains
   - Expected response format and depth

2. **Agent Selection**: Select the most appropriate agents based on:
   - Capability alignment with user needs
   - Expertise relevance to the query
   - Complementary skills for comprehensive coverage
   - Load balancing and performance considerations

3. **Workflow Determination**: Choose optimal execution pattern:
   - "single": One agent handles the entire query
   - "parallel": Multiple agents work independently on different aspects
   - "sequential": Agents work in order, each building on previous results
   - "hierarchical": Structured levels of agents with coordination
   - "pipeline": Data flows through agents in processing stages

4. **Query Decomposition**: For complex queries:
   - Break down into focused sub-questions
   - Assign each sub-question to the most suitable agent
   - Ensure sub-questions are independent and well-scoped
   - Maintain logical coherence across decomposition

RESPONSE FORMAT:
Always respond with a JSON object containing exactly these fields:
{{
  "selected_agent_ids": ["agent_id_1", "agent_id_2"],
  "selection_reasoning": "Detailed explanation of why these agents were selected (2-3 sentences)",
  "workflow": "single|parallel|sequential|hierarchical|pipeline",
  "workflow_reasoning": "Why this workflow pattern is optimal for this task (1-2 sentences)",
  "confidence_score": 0.0-1.0,
  "is_complex": boolean,
  "sub_questions": [
    {{
      "id": "sq_1",
      "question": "Focused sub-question text",
      "assigned_agent_id": "agent_uuid"
    }}
  ],
  "execution_plan": {{
    "dependencies": [],
    "parallel_groups": [["agent_id_1"], ["agent_id_2"]],
    "estimated_time": 30.0
  }}
}}

DECISION GUIDELINES:
- For simple, single-intent queries: Use "single" workflow with one agent, is_complex=false, minimal sub_questions
- For multi-intent queries: Use appropriate multi-agent workflow, is_complex=true, comprehensive decomposition
- For queries requiring different expertise: Use "parallel" or "hierarchical" workflows
- For queries with sequential dependencies: Use "sequential" or "pipeline" workflows
- Always provide execution_plan with realistic time estimates and dependency analysis

Respond only with valid JSON, no additional text."""

    return prompt


def build_consolidation_prompt(
    user_message: str,
    execution_results: List[ExecutionResult],
    config: ConsolidationConfig
) -> str:
    """
    Build result consolidation prompt for LLM.
    
    This creates a prompt for consolidating multiple agent responses
    into a unified, coherent response.
    """
    agent_responses = format_execution_results(execution_results)
    
    prompt = f"""You are an expert result consolidator responsible for intelligently merging multiple agent responses into a single, coherent, and comprehensive answer.

USER'S ORIGINAL REQUEST:
"{user_message}"

AGENT RESPONSES TO CONSOLIDATE:
{agent_responses}

CONSOLIDATION INSTRUCTIONS:
1. **Analyze Each Response**: Carefully examine each agent's response for:
   - Key insights and information
   - Unique perspectives or expertise
   - Factual accuracy and consistency
   - Completeness and relevance to the user's request

2. **Identify Relationships**: Look for:
   - Complementary information that can be combined
   - Overlapping content that can be merged
   - Conflicting information that needs resolution
   - Gaps that need to be acknowledged

3. **Synthesize Information**: Create a unified response that:
   - Directly addresses the user's original request
   - Incorporates the best insights from all agents
   - Resolves conflicts through reasoned analysis
   - Maintains accuracy and coherence
   - Provides comprehensive coverage of the topic

4. **Quality Assurance**: Ensure the consolidated response:
   - Is clear, well-structured, and easy to understand
   - Maintains appropriate tone and style
   - Includes relevant details without being overwhelming
   - Acknowledges limitations or uncertainties when appropriate

RESPONSE FORMAT:
Respond with a JSON object containing:
```json
{{
  "consolidated_content": "Your unified, comprehensive response that directly addresses the user's request",
  "consolidation_approach": "synthesis|best_selection|consensus_building|conflict_resolution",
  "confidence_score": 0.95,
  "key_insights": ["insight1", "insight2", "insight3"],
  "sources_used": ["agent1_name", "agent2_name"],
  "conflicts_resolved": ["description of any conflicts and how they were resolved"],
  "limitations": ["any limitations or uncertainties in the consolidated response"]
}}
```

Respond only with valid JSON, no additional text."""

    return prompt


def format_agent_profiles(agents: List[Agent]) -> str:
    """
    Format agent profiles for inclusion in prompts.
    
    Args:
        agents: List of available agents
        
    Returns:
        Formatted string with agent information
    """
    if not agents:
        return "No agents available"
    
    profiles = []
    for agent in agents:
        profile = f"""Agent ID: {agent.id}
Name: {agent.name}
Instruction: {agent.instruction or "No instruction available"}
Model: {agent.model}
Status: Available"""
        profiles.append(profile)
    
    return "\n\n".join(profiles)


def format_execution_results(results: List[ExecutionResult]) -> str:
    """
    Format execution results for consolidation prompts.
    
    Args:
        results: List of execution results
        
    Returns:
        Formatted string with agent responses
    """
    if not results:
        return "No execution results available"
    
    formatted_results = []
    for i, result in enumerate(results, 1):
        # Handle both ExecutionResult objects and dictionaries
        if hasattr(result, 'success'):
            # ExecutionResult object
            status = "SUCCESS" if result.success else "FAILED"
            content = result.response if result.success else f"ERROR: {result.error}"
            agent_name = result.agent_name
            agent_id = getattr(result, 'agent_id', 'unknown')
            question = getattr(result, 'question', 'N/A')
            execution_time = result.execution_time
        else:
            # Dictionary format
            status = "SUCCESS" if result.get('success', True) else "FAILED"
            content = result.get('response', 'No response')
            agent_name = result.get('agent_name', f'Agent {i}')
            agent_id = result.get('agent_id', 'unknown')
            question = result.get('question', 'N/A')
            execution_time = result.get('execution_time', 0.0)

        formatted_result = f"""Agent {i}: {agent_name} (ID: {agent_id})
Question: {question}
Status: {status}
Execution Time: {execution_time:.2f}s
Response: {content}"""

        formatted_results.append(formatted_result)
    
    return "\n\n" + "="*50 + "\n\n".join(formatted_results)


def format_workflow_context(
    workflow_pattern: str,
    agent_count: int,
    estimated_time: float
) -> str:
    """
    Format workflow context information for prompts.
    
    Args:
        workflow_pattern: Execution pattern used
        agent_count: Number of agents involved
        estimated_time: Estimated execution time
        
    Returns:
        Formatted workflow context string
    """
    return f"""WORKFLOW CONTEXT:
Pattern: {workflow_pattern.upper()}
Agents Involved: {agent_count}
Estimated Time: {estimated_time:.1f} seconds
Execution Mode: {"Multi-agent coordination" if agent_count > 1 else "Single agent"}"""


def clean_json_response(response: str) -> str:
    """
    Extract JSON content by finding opening { and closing } boundaries,
    with fallback to markdown removal if brace matching fails.

    This function uses a robust approach to extract JSON from LLM responses:
    1. First attempts to locate JSON boundaries using brace matching
    2. Handles nested objects by counting opening and closing braces
    3. Falls back to markdown removal if brace matching fails

    Args:
        response: Raw response string from agent

    Returns:
        Cleaned JSON string ready for parsing
    """
    if not response or not response.strip():
        return ""

    response = response.strip()

    # Method 1: Try to extract JSON using brace matching
    json_content = _extract_json_by_braces(response)
    if json_content:
        return json_content

    # Method 2: If brace matching failed, try after removing markdown first
    markdown_removed = _remove_markdown_blocks(response)
    if markdown_removed != response:  # Only try again if markdown was actually removed
        json_content = _extract_json_by_braces(markdown_removed)
        if json_content:
            return json_content

    # Method 3: Return the markdown-cleaned version as final fallback
    return markdown_removed


def _extract_json_by_braces(response: str) -> str:
    """
    Extract JSON content by finding the first { and matching } boundaries.

    Args:
        response: Raw response string

    Returns:
        Extracted JSON string, or empty string if no valid JSON found
    """
    # Find the first opening brace
    start_idx = response.find('{')
    if start_idx == -1:
        return ""

    # Count braces to find the matching closing brace
    brace_count = 0
    end_idx = -1

    for i in range(start_idx, len(response)):
        char = response[i]
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i
                break

    # If we found a matching closing brace, extract the JSON
    if end_idx != -1:
        json_content = response[start_idx:end_idx + 1]
        return json_content.strip()

    return ""


def _remove_markdown_blocks(response: str) -> str:
    """
    Remove markdown code blocks from response (fallback method).

    Args:
        response: Raw response string

    Returns:
        Response with markdown blocks removed
    """
    cleaned_response = response.strip()

    # Remove opening markdown markers
    if cleaned_response.startswith('```json'):
        cleaned_response = cleaned_response[7:]
    elif cleaned_response.startswith('```'):
        cleaned_response = cleaned_response[3:]

    # Remove closing markdown markers
    if cleaned_response.endswith('```'):
        cleaned_response = cleaned_response[:-3]

    return cleaned_response.strip()
