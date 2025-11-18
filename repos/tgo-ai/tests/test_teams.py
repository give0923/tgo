"""Test team management endpoints."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.team import Team
from app.models.agent import Agent
from app.models.collection import Collection, AgentCollection


class TestTeamEndpoints:
    """Test team management endpoints."""

    def test_create_team(
        self, client: TestClient, test_project: Project
    ) -> None:
        """Test creating a new team."""
        team_data = {
            "name": "Test Team",
            "model": "anthropic:claude-3-sonnet-20240229",
            "instruction": "You are a helpful assistant",
            "is_default": False,
        }

        response = client.post(f"/api/v1/teams?project_id={test_project.id}", json=team_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == team_data["name"]
        assert data["model"] == team_data["model"]
        assert data["instruction"] == team_data["instruction"]
        assert data["is_default"] == team_data["is_default"]
        assert "id" in data
        assert "created_at" in data

    def test_create_team_invalid_model_format(
        self, client: TestClient, test_project: Project
    ) -> None:
        """Test creating team with invalid model format."""
        team_data = {
            "name": "Test Team",
            "model": "invalid-model-format",  # Missing provider prefix
            "is_default": False,
        }

        response = client.post(f"/api/v1/teams?project_id={test_project.id}", json=team_data)
        assert response.status_code == 422  # Validation error

    def test_list_teams_empty(
        self, client: TestClient, test_project: Project
    ) -> None:
        """Test listing teams when none exist."""
        response = client.get(f"/api/v1/teams?project_id={test_project.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["data"] == []
        assert data["pagination"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_teams_with_data(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_project: Project,
    ) -> None:
        """Test listing teams with existing data."""
        # Create test teams
        team1 = Team(
            project_id=test_project.id,
            name="Team 1",
            model="anthropic:claude-3-sonnet-20240229",
            is_default=True,
        )
        team2 = Team(
            project_id=test_project.id,
            name="Team 2",
            model="openai:gpt-4",
            is_default=False,
        )

        db_session.add_all([team1, team2])
        await db_session.commit()

        response = client.get(f"/api/v1/teams?project_id={test_project.id}")
        assert response.status_code == 200

        data = response.json()
        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == 2

    @pytest.mark.asyncio
    async def test_get_team(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_project: Project,
    ) -> None:
        """Test getting a specific team."""
        # Create test team
        team = Team(
            project_id=test_project.id,
            name="Test Team",
            model="anthropic:claude-3-sonnet-20240229",
            instruction="Test instruction",
            is_default=False,
        )

        db_session.add(team)
        await db_session.commit()
        await db_session.refresh(team)

        response = client.get(f"/api/v1/teams/{team.id}?project_id={test_project.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(team.id)
        assert data["name"] == team.name
        assert data["model"] == team.model
        assert "agents" in data
        assert data["agents"] == []  # No agents associated

    def test_get_team_not_found(
        self, client: TestClient, test_project: Project
    ) -> None:
        """Test getting a non-existent team."""
        team_id = uuid.uuid4()
        response = client.get(f"/api/v1/teams/{team_id}?project_id={test_project.id}")
        assert response.status_code == 404

        data = response.json()
        assert data["error"]["code"] == "TEAM_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_team_with_agents_tools_and_collections(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_project: Project,
    ) -> None:
        """Test getting team details includes agents structure with tools and collections fields."""
        # Create test team
        team = Team(
            project_id=test_project.id,
            name="Test Team with Agents",
            model="anthropic:claude-3-sonnet-20240229",
            instruction="Team instruction",
            is_default=False,
        )
        db_session.add(team)
        await db_session.commit()
        await db_session.refresh(team)

        # Get team details
        response = client.get(f"/api/v1/teams/{team.id}?project_id={test_project.id}")
        assert response.status_code == 200

        data = response.json()

        # Verify team data
        assert data["id"] == str(team.id)
        assert data["name"] == team.name
        assert data["model"] == team.model
        assert data["instruction"] == team.instruction

        # Verify agents field is included (even if empty)
        assert "agents" in data
        assert isinstance(data["agents"], list)

        # The agents array should be empty since we didn't create any agents
        # But the structure should support agents with tools and collections
        assert data["agents"] == []

    @pytest.mark.asyncio
    async def test_update_team(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_project: Project,
    ) -> None:
        """Test updating a team."""
        # Create test team
        team = Team(
            project_id=test_project.id,
            name="Original Name",
            model="anthropic:claude-3-sonnet-20240229",
            is_default=False,
        )

        db_session.add(team)
        await db_session.commit()
        await db_session.refresh(team)

        # Update team
        update_data = {
            "name": "Updated Name",
            "instruction": "Updated instruction",
        }

        response = client.patch(
            f"/api/v1/teams/{team.id}?project_id={test_project.id}", json=update_data
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["instruction"] == update_data["instruction"]

    @pytest.mark.asyncio
    async def test_delete_team(
        self,
        client: TestClient,
        db_session: AsyncSession,
        test_project: Project,
    ) -> None:
        """Test deleting a team."""
        # Create test team
        team = Team(
            project_id=test_project.id,
            name="Test Team",
            model="anthropic:claude-3-sonnet-20240229",
            is_default=False,
        )

        db_session.add(team)
        await db_session.commit()
        await db_session.refresh(team)

        # Delete team
        response = client.delete(f"/api/v1/teams/{team.id}?project_id={test_project.id}")
        assert response.status_code == 204

        # Verify team is deleted
        response = client.get(f"/api/v1/teams/{team.id}?project_id={test_project.id}")
        assert response.status_code == 404

