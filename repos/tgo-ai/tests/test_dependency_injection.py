"""Test dependency injection in API endpoints."""

import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_agent_service, get_team_service
from app.exceptions import NotFoundError
from app.main import app
from app.models.project import Project
from app.services.agent_service import AgentService
from app.services.team_service import TeamService


class TestDependencyInjection:
    """Test that services are properly injected as dependencies."""

    def test_team_service_dependency_injection(self, client: TestClient, test_project: Project) -> None:
        """Test that TeamService is injected as a dependency."""
        # Create a mock service
        mock_team_service = Mock(spec=TeamService)
        mock_team_service.list_teams = AsyncMock(return_value=([], 0))

        # Override the dependency
        app.dependency_overrides[get_team_service] = lambda: mock_team_service

        try:
            # Make request
            response = client.get(
                f"/api/v1/teams?project_id={test_project.id}"
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["data"] == []
            assert data["pagination"]["total"] == 0

            # Verify service was called
            mock_team_service.list_teams.assert_called_once()

        finally:
            # Clean up
            if get_team_service in app.dependency_overrides:
                del app.dependency_overrides[get_team_service]

    def test_agent_service_dependency_injection(self, client: TestClient, test_project: Project) -> None:
        """Test that AgentService is injected as a dependency."""
        # Create a mock service
        mock_agent_service = Mock(spec=AgentService)
        mock_agent_service.list_agents = AsyncMock(return_value=([], 0))

        # Override the dependency
        app.dependency_overrides[get_agent_service] = lambda: mock_agent_service

        try:
            # Make request
            response = client.get(
                f"/api/v1/agents?project_id={test_project.id}",
            )

            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["data"] == []
            assert data["pagination"]["total"] == 0

            # Verify service was called
            mock_agent_service.list_agents.assert_called_once()

        finally:
            # Clean up
            if get_agent_service in app.dependency_overrides:
                del app.dependency_overrides[get_agent_service]

    def test_service_receives_correct_parameters(self, client: TestClient, test_project: Project) -> None:
        """Test that services receive correct parameters from dependency injection."""
        # Create a mock service
        mock_team_service = Mock(spec=TeamService)
        mock_team_service.list_teams = AsyncMock(return_value=([], 0))

        # Override the dependency
        app.dependency_overrides[get_team_service] = lambda: mock_team_service

        try:
            # Make request with parameters
            response = client.get(
                f"/api/v1/teams?project_id={test_project.id}&is_default=true&limit=10&offset=5"
            )

            # Verify response
            assert response.status_code == 200

            # Verify service was called with correct parameters
            mock_team_service.list_teams.assert_called_once_with(
                project_id=test_project.id,
                is_default=True,
                limit=10,
                offset=5,
            )

        finally:
            # Clean up
            if get_team_service in app.dependency_overrides:
                del app.dependency_overrides[get_team_service]

    def test_multiple_endpoints_use_same_service_instance(self, client: TestClient, test_project: Project) -> None:
        """Test that the same service instance is used within a request."""
        # This test verifies that the dependency injection system works correctly
        # and that services are properly scoped

        # Create a mock service that tracks calls
        call_count = 0

        def create_mock_service():
            nonlocal call_count
            call_count += 1
            mock_service = Mock(spec=TeamService)
            mock_service.get_team = AsyncMock(side_effect=NotFoundError("Team", uuid.uuid4()))
            mock_service.call_id = call_count  # Track which instance this is
            return mock_service

        # Override the dependency
        app.dependency_overrides[get_team_service] = create_mock_service

        try:
            # Make request that should fail (team not found)
            team_id = uuid.uuid4()
            response = client.get(
                f"/api/v1/teams/{team_id}?project_id={test_project.id}"
            )

            # Verify that only one service instance was created for this request
            assert call_count == 1
            assert response.status_code == 404  # NotFoundError handling

        finally:
            # Clean up
            if get_team_service in app.dependency_overrides:
                del app.dependency_overrides[get_team_service]
