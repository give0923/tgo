"""Test development environment features."""

import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth.api_key import get_project_from_api_key
from app.config import settings
from app.dev_seed import seed_development_data, seed_development_project
from app.main import app
from app.models.project import Project


class TestDevelopmentSeeding:
    """Test development environment seeding functionality."""

    @pytest.mark.asyncio
    async def test_seed_development_project_creates_project(self, db_session) -> None:
        """Test that development project is created when it doesn't exist."""
        # Ensure we're in development mode
        with patch.object(settings, 'environment', 'development'):
            await seed_development_project(db_session)
            
            # Verify project was created
            from sqlalchemy import select
            stmt = select(Project).where(Project.api_key == "dev")
            result = await db_session.execute(stmt)
            project = result.scalar_one_or_none()
            
            assert project is not None
            assert project.name == "Development Project"
            assert project.api_key == "dev"

    @pytest.mark.asyncio
    async def test_seed_development_project_skips_existing(self, db_session) -> None:
        """Test that seeding skips if development project already exists."""
        # Create existing development project
        existing_project = Project(
            id=uuid.uuid4(),
            name="Existing Dev Project",
            api_key="dev",
        )
        db_session.add(existing_project)
        await db_session.commit()
        
        with patch.object(settings, 'environment', 'development'):
            await seed_development_project(db_session)
            
            # Verify original project is unchanged
            from sqlalchemy import select
            stmt = select(Project).where(Project.api_key == "dev")
            result = await db_session.execute(stmt)
            project = result.scalar_one_or_none()
            
            assert project.name == "Existing Dev Project"  # Original name preserved

    @pytest.mark.asyncio
    async def test_seed_development_project_skips_production(self, db_session) -> None:
        """Test that seeding is skipped in production environment."""
        with patch.object(settings, 'environment', 'production'):
            await seed_development_project(db_session)
            
            # Verify no project was created
            from sqlalchemy import select
            stmt = select(Project).where(Project.api_key == "dev")
            result = await db_session.execute(stmt)
            project = result.scalar_one_or_none()
            
            assert project is None


class TestDevelopmentAuthentication:
    """Test development API key authentication."""

    @pytest.mark.asyncio
    async def test_dev_api_key_works_in_development(self, db_session) -> None:
        """Test that 'dev' API key works in development environment."""
        # Create development project
        dev_project = Project(
            id=uuid.uuid4(),
            name="Development Project",
            api_key="dev",
        )
        db_session.add(dev_project)
        await db_session.commit()
        
        with patch.object(settings, 'environment', 'development'):
            project = await get_project_from_api_key("dev", db_session)
            assert project.name == "Development Project"
            assert project.api_key == "dev"

    @pytest.mark.asyncio
    async def test_dev_api_key_rejected_in_production(self, db_session) -> None:
        """Test that 'dev' API key is rejected in production environment."""
        with patch.object(settings, 'environment', 'production'):
            with pytest.raises(Exception) as exc_info:
                await get_project_from_api_key("dev", db_session)
            
            assert "Development API key is only valid in development environment" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_dev_api_key_missing_project(self, db_session) -> None:
        """Test error when development project doesn't exist."""
        with patch.object(settings, 'environment', 'development'):
            with pytest.raises(Exception) as exc_info:
                await get_project_from_api_key("dev", db_session)
            
            assert "Development project not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_standard_api_key_still_works(self, db_session) -> None:
        """Test that standard API keys still work normally."""
        # Create standard project
        project = Project(
            id=uuid.uuid4(),
            name="Standard Project",
            api_key="ak_test123",
        )
        db_session.add(project)
        await db_session.commit()
        
        result = await get_project_from_api_key("ak_test123", db_session)
        assert result.name == "Standard Project"


class TestDevelopmentAPIIntegration:
    """Test API integration with development features."""

    @pytest.mark.asyncio
    async def test_dev_api_key_in_api_endpoints(self, client: TestClient, db_session) -> None:
        """Test that development API key works with actual API endpoints."""
        # Create development project in test database
        from app.models.project import Project
        dev_project = Project(
            id=uuid.uuid4(),
            name="Development Project",
            api_key="dev",
        )
        db_session.add(dev_project)
        await db_session.commit()

        # Mock environment to be development
        with patch.object(settings, 'environment', 'development'):
            # Test API endpoint with dev key
            response = client.get(
                f"/api/v1/teams?project_id={dev_project.id}"
            )

            assert response.status_code == 200
            data = response.json()
            assert "data" in data
            assert "pagination" in data

    def test_openapi_has_no_legacy_auth_schemes(self, client: TestClient) -> None:
        """OpenAPI should not advertise legacy authentication schemes (BearerAuth/ApiKeyAuth)."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_schema = response.json()

        # Legacy schemes should be absent
        if "securitySchemes" in openapi_schema.get("components", {}):
            security_schemes = openapi_schema["components"]["securitySchemes"]
            assert "BearerAuth" not in security_schemes
            assert "ApiKeyAuth" not in security_schemes

    def test_endpoints_do_not_require_legacy_auth(self, client: TestClient) -> None:
        """Endpoints should not require legacy authentication (BearerAuth/ApiKeyAuth)."""
        response = client.get("/openapi.json")
        openapi_schema = response.json()

        teams_get = openapi_schema["paths"]["/api/v1/teams"]["get"]
        security = teams_get.get("security", [])

        # Ensure legacy auth requirements are not present
        assert {"BearerAuth": []} not in security
        assert {"ApiKeyAuth": []} not in security
