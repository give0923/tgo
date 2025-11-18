"""
Development utilities for the RAG service.
"""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .database import get_db_session
from .models.projects import Project

logger = structlog.get_logger(__name__)

# Development project constants
DEV_PROJECT_NAME = "Development Project"
DEV_API_KEY = "dev"


async def create_development_project() -> None:
    """
    Create a default development project if it doesn't exist.
    
    This function creates a development project with a hardcoded API key
    that can be used for local development. The project is only created
    when the environment is set to "development".
    
    Raises:
        Exception: If project creation fails
    """
    settings = get_settings()
    
    # Only create development project in development environment
    if settings.environment.lower() != "development":
        logger.debug(
            "Skipping development project creation",
            environment=settings.environment,
            reason="Not in development environment"
        )
        return
    
    try:
        async with get_db_session() as db:
            # Check if development project already exists
            query = select(Project).where(
                Project.api_key == DEV_API_KEY,
                Project.deleted_at.is_(None)
            )
            
            result = await db.execute(query)
            existing_project = result.scalar_one_or_none()
            
            if existing_project:
                logger.debug(
                    "Development project already exists",
                    project_id=str(existing_project.id),
                    project_name=existing_project.name,
                    api_key=DEV_API_KEY
                )
                return
            
            # Create new development project
            dev_project = Project(
                name=DEV_PROJECT_NAME,
                api_key=DEV_API_KEY
            )
            
            db.add(dev_project)
            await db.commit()
            await db.refresh(dev_project)
            
            logger.info(
                "Development project created successfully",
                project_id=str(dev_project.id),
                project_name=dev_project.name,
                api_key=DEV_API_KEY,
                environment=settings.environment
            )
            
    except Exception as e:
        logger.error(
            "Failed to create development project",
            error=str(e),
            environment=settings.environment
        )
        raise


def is_development_api_key(api_key: str) -> bool:
    """
    Check if the provided API key is the development API key.
    
    Args:
        api_key: API key to check
        
    Returns:
        True if the API key is the development API key
    """
    return api_key == DEV_API_KEY


def is_development_environment() -> bool:
    """
    Check if the current environment is development.
    
    Returns:
        True if the environment is set to "development"
    """
    settings = get_settings()
    return settings.environment.lower() == "development"


def validate_development_api_key_usage(api_key: str) -> tuple[bool, str]:
    """
    Validate that the development API key is only used in development environment.
    
    Args:
        api_key: API key to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if the API key usage is valid
        - error_message: Error message if usage is invalid, empty string if valid
    """
    if not is_development_api_key(api_key):
        # Not a development API key, no restrictions
        return True, ""
    
    if is_development_environment():
        # Development API key in development environment is valid
        return True, ""
    
    # Development API key in non-development environment is invalid
    settings = get_settings()
    error_message = (
        f"Development API key 'dev' is not allowed in {settings.environment} environment. "
        "Please use a proper project API key for non-development environments."
    )
    
    return False, error_message


async def ensure_development_setup() -> None:
    """
    Ensure development environment is properly set up.
    
    This function is called during application startup to set up
    development-specific resources like the default development project.
    """
    settings = get_settings()
    
    if settings.environment.lower() == "development":
        logger.info("Setting up development environment")
        await create_development_project()
        logger.info("Development environment setup complete")
    else:
        logger.debug(
            "Skipping development setup",
            environment=settings.environment
        )
