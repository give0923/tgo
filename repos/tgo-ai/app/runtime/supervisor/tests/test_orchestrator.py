"""
Tests for the coordination orchestrator.

This module contains comprehensive tests for the main orchestrator
including unit tests, integration tests, and error handling scenarios.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.models.internal import CoordinationContext, Team, Agent
from app.runtime.supervisor.infrastructure.services import AIServiceClient
from app.runtime.supervisor.infrastructure.services import AgentServiceClient

from ..core.orchestrator import CoordinationOrchestrator
from ..models.coordination import CoordinationRequest, QueryAnalysisResult, SubQuestion, ExecutionPlan
from ..models.execution import ExecutionResult, WorkflowPlan, AgentExecution, WorkflowPattern
from ..models.results import ConsolidationResult, ConsolidationStrategy
from ..configuration.settings import CoordinationConfig
from ..exceptions.coordination import CoordinationError


class TestCoordinationOrchestrator:
    """Test suite for CoordinationOrchestrator."""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI service client."""
        mock = Mock(spec=AIServiceClient)
        mock.generate_response = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_agent_service(self):
        """Mock agent service client."""
        mock = Mock(spec=AgentServiceClient)
        mock.execute_agent = AsyncMock()
        return mock
    
    @pytest.fixture
    def sample_team(self):
        """Sample team with agents."""
        agents = [
            Agent(
                id="agent-1",
                name="Sales Expert",
                description="Expert in sales and customer relations",
                capabilities=["sales", "customer_service"],
                is_active=True
            ),
            Agent(
                id="agent-2", 
                name="Technical Expert",
                description="Expert in technical support and troubleshooting",
                capabilities=["technical_support", "troubleshooting"],
                is_active=True
            )
        ]
        
        return Team(
            id="team-1",
            name="Customer Support Team",
            instruction="Provide excellent customer support",
            agents=agents
        )
    
    @pytest.fixture
    def sample_context(self, sample_team):
        """Sample coordination context."""
        return CoordinationContext(
            team=sample_team,
            message="I need help with my product that stopped working and want to know about warranty",
            session_id="session-123",
            user_id="user-456",
            execution_strategy="optimal",
            max_agents=2,
            timeout=300,
            require_consensus=False
        )
    
    @pytest.fixture
    def sample_request(self, sample_context):
        """Sample coordination request."""
        return CoordinationRequest(
            context=sample_context,
            auth_headers={"Authorization": "Bearer test-token"}
        )
    
    @pytest.fixture
    def orchestrator(self, mock_ai_service, mock_agent_service):
        """Coordination orchestrator with mocked dependencies."""
        config = CoordinationConfig()
        return CoordinationOrchestrator(
            ai_service_client=mock_ai_service,
            agent_service_client=mock_agent_service,
            config=config
        )
    
    @pytest.mark.asyncio
    async def test_successful_coordination_workflow(
        self, orchestrator, sample_request, mock_ai_service, mock_agent_service
    ):
        """Test successful end-to-end coordination workflow."""
        # Mock query analysis response
        mock_ai_service.generate_response.return_value = '''
        {
            "selected_agent_ids": ["agent-1", "agent-2"],
            "selection_reasoning": "Need both sales and technical expertise",
            "workflow": "parallel",
            "workflow_reasoning": "Issues are independent and can be handled in parallel",
            "confidence_score": 0.9,
            "is_complex": true,
            "sub_questions": [
                {
                    "id": "sq_1",
                    "question": "What is the warranty status for this product?",
                    "assigned_agent_id": "agent-1"
                },
                {
                    "id": "sq_2", 
                    "question": "How can I troubleshoot the product that stopped working?",
                    "assigned_agent_id": "agent-2"
                }
            ],
            "execution_plan": {
                "dependencies": [],
                "parallel_groups": [["agent-1"], ["agent-2"]],
                "estimated_time": 25.0
            }
        }
        '''
        
        # Mock agent execution responses
        from app.models.internal import AgentExecutionResponse
        
        mock_agent_service.execute_agent.side_effect = [
            AgentExecutionResponse(
                success=True,
                response="Your product is covered under a 2-year warranty. You can file a claim through our warranty portal.",
                execution_time=12.5,
                agent_id="agent-1"
            ),
            AgentExecutionResponse(
                success=True,
                response="Try these troubleshooting steps: 1) Check power connection, 2) Reset the device, 3) Update firmware.",
                execution_time=15.2,
                agent_id="agent-2"
            )
        ]
        
        # Mock consolidation response
        mock_ai_service.generate_response.side_effect = [
            mock_ai_service.generate_response.return_value,  # Query analysis
            '''
            {
                "consolidated_content": "Your product issue can be addressed in two ways: First, your product is covered under a 2-year warranty and you can file a claim through our warranty portal. Second, you can try these troubleshooting steps: check power connection, reset the device, and update firmware. If troubleshooting doesn't work, proceed with the warranty claim.",
                "consolidation_approach": "synthesis",
                "confidence_score": 0.95,
                "key_insights": ["Product has warranty coverage", "Multiple troubleshooting options available", "Clear escalation path"],
                "sources_used": ["Sales Expert", "Technical Expert"],
                "conflicts_resolved": [],
                "limitations": []
            }
            '''
        ]
        
        # Execute coordination
        response = await orchestrator.coordinate(sample_request)
        
        # Verify response
        assert response.success is True
        assert response.request_id == sample_request.request_id
        assert "warranty" in response.consolidated_response.lower()
        assert "troubleshooting" in response.consolidated_response.lower()
        assert len(response.execution_results) == 2
        assert response.metadata["agents_consulted"] == 2
        assert response.metadata["successful_agents"] == 2
        assert response.metadata["workflow_pattern"] == "parallel"
        assert response.metadata["is_complex_query"] is True
    
    @pytest.mark.asyncio
    async def test_simple_single_agent_workflow(
        self, orchestrator, sample_request, mock_ai_service, mock_agent_service
    ):
        """Test simple single-agent workflow."""
        # Update request for simple query
        sample_request.context.message = "What are your business hours?"
        
        # Mock simple query analysis
        mock_ai_service.generate_response.return_value = '''
        {
            "selected_agent_ids": ["agent-1"],
            "selection_reasoning": "Simple information query suitable for sales agent",
            "workflow": "single",
            "workflow_reasoning": "Single agent can handle this straightforward question",
            "confidence_score": 0.95,
            "is_complex": false,
            "sub_questions": [
                {
                    "id": "sq_1",
                    "question": "What are your business hours?",
                    "assigned_agent_id": "agent-1"
                }
            ],
            "execution_plan": {
                "dependencies": [],
                "parallel_groups": [["agent-1"]],
                "estimated_time": 10.0
            }
        }
        '''
        
        # Mock agent response
        from app.models.internal import AgentExecutionResponse
        mock_agent_service.execute_agent.return_value = AgentExecutionResponse(
            success=True,
            response="Our business hours are Monday-Friday 9 AM to 6 PM, and Saturday 10 AM to 4 PM.",
            execution_time=8.3,
            agent_id="agent-1"
        )
        
        # Mock consolidation (simple case)
        mock_ai_service.generate_response.side_effect = [
            mock_ai_service.generate_response.return_value,  # Query analysis
            '''
            {
                "consolidated_content": "Our business hours are Monday-Friday 9 AM to 6 PM, and Saturday 10 AM to 4 PM.",
                "consolidation_approach": "best_selection",
                "confidence_score": 0.98,
                "key_insights": ["Clear business hours provided"],
                "sources_used": ["Sales Expert"],
                "conflicts_resolved": [],
                "limitations": []
            }
            '''
        ]
        
        # Execute coordination
        response = await orchestrator.coordinate(sample_request)
        
        # Verify response
        assert response.success is True
        assert len(response.execution_results) == 1
        assert response.metadata["workflow_pattern"] == "single"
        assert response.metadata["is_complex_query"] is False
        assert "business hours" in response.consolidated_response.lower()
    
    @pytest.mark.asyncio
    async def test_coordination_with_agent_failure(
        self, orchestrator, sample_request, mock_ai_service, mock_agent_service
    ):
        """Test coordination handling when some agents fail."""
        # Mock query analysis for parallel execution
        mock_ai_service.generate_response.return_value = '''
        {
            "selected_agent_ids": ["agent-1", "agent-2"],
            "selection_reasoning": "Need both agents for comprehensive response",
            "workflow": "parallel",
            "workflow_reasoning": "Can execute in parallel",
            "confidence_score": 0.85,
            "is_complex": true,
            "sub_questions": [
                {
                    "id": "sq_1",
                    "question": "Handle sales aspect",
                    "assigned_agent_id": "agent-1"
                },
                {
                    "id": "sq_2",
                    "question": "Handle technical aspect", 
                    "assigned_agent_id": "agent-2"
                }
            ],
            "execution_plan": {
                "dependencies": [],
                "parallel_groups": [["agent-1"], ["agent-2"]],
                "estimated_time": 20.0
            }
        }
        '''
        
        # Mock mixed agent responses (one success, one failure)
        from app.models.internal import AgentExecutionResponse
        mock_agent_service.execute_agent.side_effect = [
            AgentExecutionResponse(
                success=True,
                response="Sales information provided successfully.",
                execution_time=10.0,
                agent_id="agent-1"
            ),
            AgentExecutionResponse(
                success=False,
                response="",
                execution_time=5.0,
                agent_id="agent-2",
                error="Agent temporarily unavailable"
            )
        ]
        
        # Mock consolidation with partial results
        mock_ai_service.generate_response.side_effect = [
            mock_ai_service.generate_response.return_value,  # Query analysis
            '''
            {
                "consolidated_content": "Based on available information: Sales information provided successfully. Note: Technical information is currently unavailable due to system issues.",
                "consolidation_approach": "best_selection",
                "confidence_score": 0.7,
                "key_insights": ["Partial information available"],
                "sources_used": ["Sales Expert"],
                "conflicts_resolved": [],
                "limitations": ["Technical agent unavailable", "Incomplete response"]
            }
            '''
        ]
        
        # Execute coordination
        response = await orchestrator.coordinate(sample_request)
        
        # Verify response handles partial failure gracefully
        assert response.success is True  # Should still succeed with partial results
        assert len(response.execution_results) == 2
        assert response.metadata["successful_agents"] == 1
        assert response.metadata["total_executions"] == 2
        assert "unavailable" in response.consolidated_response.lower()
    
    @pytest.mark.asyncio
    async def test_coordination_error_handling(
        self, orchestrator, sample_request, mock_ai_service
    ):
        """Test coordination error handling."""
        # Mock AI service failure
        mock_ai_service.generate_response.side_effect = Exception("AI service unavailable")
        
        # Execute coordination
        response = await orchestrator.coordinate(sample_request)
        
        # Verify error response
        assert response.success is False
        assert response.error is not None
        assert "error" in response.message.lower()
        assert len(response.execution_results) == 0
        assert response.metadata["error_occurred"] is True
