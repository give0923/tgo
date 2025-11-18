"""
System-level agents for coordination system v2.

This module provides specialized system agents that are used internally
by the coordination system for query analysis and result consolidation.
"""

from datetime import datetime
from uuid import uuid4
from typing import Dict, Any

from app.config import settings as app_settings
from app.models.internal import Agent
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_result_consolidation_instruction(streaming: bool = False) -> str:
    """Build result consolidation system instruction with optional streaming wording."""
    persona_block = """你现在是“小T”，一名干净利落的暖心智能客服助手。任何时候都要：
- 直接给出用户最关心的结论。
- 用简短的共情语句回应用户情绪，例如“我理解这真的让人着急”。
- 保持积极、礼貌、乐于助人的口吻，使用“您”“咱们”等表达。
- 先结论，再补充必要细节，必要时用简短分点说明。
- 回答末尾主动询问是否需要进一步帮助。
- 语气自然口语化，但避免过度随意；适度使用 🙂、👍 等表情。
- 遇到信息不足时直说“不确定”，并建议联系人工客服，绝不凭空编造。
- 不评价用户本人，不使用“系统显示”这类冰冷措辞，而用“我看到”“我查到”。
"""

    analysis_block = """合并多名智能体的回复时，请：
- 找出共同结论并突出关键差异；
- 如果存在冲突，说明冲突点并给出您的判断依据；
- 保留原始信息来源或智能体名称，便于追溯；
- 明确指出仍需确认或存在不确定的部分。"""

    if streaming:
        format_block = """回复要求（流式输出）：
- 以“您好！我是小T...”开场，并立即给出结论。
- 采用自然语言段落或简洁分点，保证可逐步播报。
- 语句口语化但专业，适度使用语气词和表情符号（例如“别担心，我帮您看看哦 🙂”）。
- 结尾询问“还有其他需要我帮您的吗？”之类的主动关怀。
- 严禁使用 JSON、代码块或生硬的格式。"""
    else:
        format_block = """回复要求（结构化输出）：
请返回一个 JSON 对象，字段如下：
{
  "consolidated_content": "正文，必须遵循小T的口吻，先结论后细节，可包含分点说明",
  "consolidation_approach": "synthesis|best_selection|consensus_building|conflict_resolution",
  "confidence_score": 介于 0 和 1 之间的数字，体现您对结论的把握程度,
  "key_insights": ["关键结论或提示，符合小T话风"],
  "sources_used": ["引用到的智能体名称或信息来源"],
  "conflicts_resolved": ["若存在冲突，请描述如何处理"],
  "limitations": ["说明仍需进一步确认的内容或无法处理的部分"],
  "follow_up_question": "请以小T的语气主动询问用户是否还需要协助"
}
除 JSON 外不要输出任何额外文本，字段内容需符合小T的语言风格。"""

    return "\n\n".join([persona_block, analysis_block, format_block])


def create_query_analysis_agent() -> Agent:
    """
    Create a specialized agent for query analysis and decomposition.
    
    This agent is responsible for:
    - Analyzing user queries to understand intent and complexity
    - Decomposing multi-intent queries into focused sub-questions
    - Selecting appropriate agents based on capabilities
    - Determining optimal workflow execution patterns
    - Creating detailed execution plans with dependencies
    
    Returns:
        Agent: Configured query analysis agent
    """
    settings = app_settings.supervisor_runtime
    qa = settings.coordination.query_analysis

    logger.debug(
        "Creating query analysis agent",
        model_name=qa.model_name,
        temperature=qa.temperature,
        max_tokens=qa.max_tokens
    )

    return Agent(
        id=uuid4(),
        name="Query Analysis Agent",
        instruction="""You are an expert AI coordination system responsible for intelligent agent selection, task decomposition, and workflow orchestration. Your task is to analyze user queries and create comprehensive coordination plans.

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
{
  "selected_agent_ids": ["agent_id_1", "agent_id_2"],
  "selection_reasoning": "Detailed explanation of why these agents were selected (2-3 sentences)",
  "workflow": "single|parallel|sequential|hierarchical|pipeline",
  "workflow_reasoning": "Why this workflow pattern is optimal for this task (1-2 sentences)",
  "confidence_score": 0.0-1.0,
  "is_complex": boolean,
  "sub_questions": [
    {
      "id": "sq_1",
      "question": "Focused sub-question text",
      "assigned_agent_id": "agent_uuid"
    }
  ],
  "execution_plan": {
    "dependencies": [],
    "parallel_groups": [["agent_id_1"], ["agent_id_2"]],
    "estimated_time": 30.0
  }
}

DECISION GUIDELINES:
- For simple, single-intent queries: Use "single" workflow with one agent, is_complex=false, minimal sub_questions
- For multi-intent queries: Use appropriate multi-agent workflow, is_complex=true, comprehensive decomposition
- For queries requiring different expertise: Use "parallel" or "hierarchical" workflows
- For queries with sequential dependencies: Use "sequential" or "pipeline" workflows
- Always provide execution_plan with realistic time estimates and dependency analysis

Respond only with valid JSON, no additional text.""",
        model=qa.model_name,
        config={
            "temperature": qa.temperature,
            "max_tokens": qa.max_tokens,
            "system_agent": True,
            "role": "query_analysis",
        },
        team_id=None,
        tools=[],
        collections=[],
        is_default=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


def create_result_consolidation_agent(streaming: bool = False) -> Agent:
    """
    Create a specialized agent for result consolidation and synthesis.
    
    This agent is responsible for:
    - Analyzing multiple agent responses for consistency
    - Identifying and resolving conflicts between responses
    - Synthesizing information into coherent unified responses
    - Maintaining source attribution and confidence scoring
    - Providing comprehensive conflict resolution
    
    Returns:
        Agent: Configured result consolidation agent
    """
    settings = app_settings.supervisor_runtime
    consolidation = settings.coordination.result_consolidation
    return Agent(
        id=uuid4(),
        name="Result Consolidation Agent",
        instruction=get_result_consolidation_instruction(streaming=streaming),
        model=consolidation.model_name,
        config={
            "temperature": consolidation.temperature,
            "max_tokens": consolidation.max_tokens,
            "system_agent": True,
            "role": "result_consolidation",
        },
        team_id=None,
        tools=[],
        collections=[],
        is_default=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


def get_system_agent_by_type(agent_type: str, *, streaming: bool = False) -> Agent:
    """
    Get a system agent by type.
    
    Args:
        agent_type: Type of system agent ("query_analysis" or "result_consolidation")
        streaming: When True and requesting the result consolidation agent, tailor
            the instructions for streaming responses (no JSON payload)
        
    Returns:
        Agent: The requested system agent
        
    Raises:
        ValueError: If agent_type is not recognized
    """
    if agent_type == "query_analysis":
        return create_query_analysis_agent()
    elif agent_type == "result_consolidation":
        return create_result_consolidation_agent(streaming=streaming)
    else:
        raise ValueError(f"Unknown system agent type: {agent_type}")


def create_system_agents() -> Dict[str, Agent]:
    """
    Create all system agents used by the coordination system.
    
    Returns:
        Dict[str, Agent]: Dictionary mapping agent types to agent instances
    """
    return {
        "query_analysis": create_query_analysis_agent(),
        "result_consolidation": create_result_consolidation_agent()
    }
