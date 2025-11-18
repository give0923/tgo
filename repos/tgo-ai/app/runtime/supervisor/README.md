# TGO Supervisor Agent - Coordination System v2

A completely refactored coordination system with clean architecture, comprehensive error handling, and robust multi-agent workflow support.

## Overview

The Coordination System v2 is a complete rewrite of the original coordination system, designed with modern software engineering principles and clean architecture patterns. It provides intelligent multi-agent coordination with LLM-powered query decomposition, workflow optimization, and result consolidation.

## Key Features

### 🧠 Intelligent Query Analysis
- **LLM-powered decomposition**: Automatically breaks down complex multi-intent queries
- **Smart agent assignment**: Matches sub-questions to the most suitable agents
- **Workflow pattern detection**: Determines optimal execution patterns (parallel, sequential, hierarchical)
- **Confidence scoring**: Provides reliability metrics for all decisions

### 🔄 Multiple Workflow Patterns
- **Single**: One agent handles the entire query
- **Parallel**: Multiple agents work independently on different aspects
- **Sequential**: Agents work in order, each building on previous results
- **Hierarchical**: Structured levels of agents with coordination
- **Pipeline**: Data flows through agents in processing stages

### 🎯 Advanced Result Consolidation
- **LLM-powered synthesis**: Intelligently merges multiple agent responses
- **Conflict detection**: Identifies and resolves contradictions between responses
- **Consensus building**: Creates unified responses from diverse perspectives
- **Source attribution**: Maintains transparency about information sources

### 🏗️ Clean Architecture
- **Dependency injection**: All components are easily testable and replaceable
- **Interface-based design**: Clear contracts between all components
- **Type-safe models**: Comprehensive data validation throughout
- **Separation of concerns**: Each component has a single, well-defined responsibility

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CoordinationOrchestrator                 │
│                     (Main Entry Point)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│QueryAnalyzer│ │WorkflowPlan │ │ExecutionMgr │
│             │ │ner          │ │             │
└─────────────┘ └─────────────┘ └─────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
                      ▼
              ┌─────────────┐
              │ResultConsol │
              │idator       │
              └─────────────┘
```

## Core Logic Flow

1. **Query Analysis** (`QueryAnalyzer`)
   - Use LLM to decompose user queries into sub-questions
   - Assign sub-questions to appropriate agents
   - Return structured coordination plan in exact JSON format

2. **Workflow Planning** (`WorkflowPlanner`)
   - Take LLM coordination plan and create executable workflow
   - Handle dependency analysis and parallel group optimization
   - Create execution timeline and resource allocation

3. **Execution Management** (`ExecutionManager`)
   - Distribute sub-questions to assigned agents following workflow pattern
   - Support multiple execution patterns with proper coordination
   - Handle timeouts, retries, and error recovery
   - Collect execution results from all agents

4. **Result Consolidation** (`ResultConsolidator`)
   - Use LLM to consolidate and summarize results
   - Handle conflict resolution and consensus building
   - Return final consolidated response

## LLM Response Format

The system uses a standardized JSON format for LLM responses:

```json
{
  "selected_agent_ids": ["99010ace-aa82-46a1-bdb4-04254fa55b6f", "20509606-ee81-4ae7-ac8d-c977834dc6be"],
  "selection_reasoning": "用户查询包含两个独立意图：售后问题（手表不动了）和售前问题（购买新手表的价格），需要分别由售后专家张三和售前专家李四处理",
  "workflow": "parallel",
  "workflow_reasoning": "两个问题相互独立无依赖关系，可以并行处理以提高效率",
  "confidence_score": 0.9,
  "is_complex": true,
  "sub_questions": [
    {
      "id": "sq_1",
      "question": "我购买的手表不动了，应该怎么办？",
      "assigned_agent_id": "99010ace-aa82-46a1-bdb4-04254fa55b6f"
    },
    {
      "id": "sq_2",
      "question": "我想再买一个手表，现在价格是多少？",
      "assigned_agent_id": "20509606-ee81-4ae7-ac8d-c977834dc6be"
    }
  ],
  "execution_plan": {
    "dependencies": [],
    "parallel_groups": [["99010ace-aa82-46a1-bdb4-04254fa55b6f"], ["20509606-ee81-4ae7-ac8d-c977834dc6be"]],
    "estimated_time": 20.0
  }
}
```

## Usage Example

```python
from app.runtime.supervisor.orchestration import CoordinationOrchestrator
from app.runtime.supervisor.models import CoordinationRequest
from app.models.internal import CoordinationContext, Team

# Initialize orchestrator
orchestrator = CoordinationOrchestrator(
    ai_service_client=ai_service,
    agent_service_client=agent_service
)

# Create coordination request
request = CoordinationRequest(
    context=CoordinationContext(
        team=your_team,
        message="我购买的手表不动了，应该怎么办？另外我想再买一个手表，现在价格是多少？",
        max_agents=3,
        timeout=300
    ),
    auth_headers={"Authorization": "Bearer your-token"}
)

# Execute coordination
response = await orchestrator.coordinate(request)

# Access results
print(f"Success: {response.success}")
print(f"Consolidated Response: {response.consolidated_response}")
print(f"Agents Used: {response.metadata['agents_consulted']}")
```

## Configuration

The system is highly configurable through environment variables:

```bash
# Query Analysis Configuration
COORDINATION_V2_QUERY_ANALYSIS_MODEL_NAME=anthropic:claude-3-sonnet-20240229
COORDINATION_V2_QUERY_ANALYSIS_TEMPERATURE=0.2
COORDINATION_V2_QUERY_ANALYSIS_MAX_TOKENS=2000

# Execution Configuration
COORDINATION_V2_EXECUTION_DEFAULT_TIMEOUT=300
COORDINATION_V2_EXECUTION_MAX_CONCURRENT=20

# Consolidation Configuration
COORDINATION_V2_CONSOLIDATION_MODEL_NAME=anthropic:claude-3-sonnet-20240229
COORDINATION_V2_CONSOLIDATION_TEMPERATURE=0.3

# Global Settings
COORDINATION_V2_LOG_LEVEL=INFO
COORDINATION_V2_ENABLE_CACHING=true
```

## Testing

The system includes comprehensive tests:

```bash
# Run all tests
pytest app/coordinationv2/tests/

# Run specific test file
pytest app/coordinationv2/tests/test_orchestrator.py

# Run with coverage
pytest app/runtime/supervisor/tests/ --cov=app.runtime.supervisor
```

## Performance Features

- **Caching**: Intelligent caching of LLM responses and agent profiles
- **Parallel Execution**: Optimized concurrent agent execution
- **Metrics Collection**: Comprehensive performance monitoring
- **Resource Management**: Memory and CPU usage optimization
- **Timeout Handling**: Graceful handling of long-running operations

## Error Handling

The system provides comprehensive error handling:

- **Specific Exception Types**: Different exceptions for different failure modes
- **Error Recovery**: Automatic retry mechanisms for transient failures
- **Graceful Degradation**: Partial results when some agents fail
- **Detailed Logging**: Structured logging with correlation IDs

## Migration from v1

The new system is designed to be a drop-in replacement for the original coordination system. Key differences:

1. **Cleaner API**: Simplified interfaces and better type safety
2. **Better Error Handling**: More specific exceptions and recovery mechanisms
3. **Enhanced Performance**: Optimized execution patterns and caching
4. **Improved Testing**: Comprehensive test suite with mocking support
5. **Better Monitoring**: Detailed metrics and structured logging

## Contributing

When contributing to the coordination system:

1. Follow the established architecture patterns
2. Add comprehensive tests for new functionality
3. Update documentation for API changes
4. Use type hints throughout
5. Follow the existing error handling patterns

## License

This coordination system is part of the TGO Supervisor Agent project.
