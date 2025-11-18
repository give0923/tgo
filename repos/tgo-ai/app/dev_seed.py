"""Development environment seeding utilities."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.project import Project


async def seed_development_project(db: AsyncSession) -> None:
    """
    Seed development project if running in development environment.
    
    Creates a project with api_key="dev" for development convenience.
    Only runs in development environment and only creates the project once.
    
    Args:
        db: Database session
    """
    if not settings.is_development:
        return
    
    # Check if development project already exists
    stmt = select(Project).where(Project.api_key == "dev")
    result = await db.execute(stmt)
    existing_project = result.scalar_one_or_none()
    
    if existing_project:
        # Development project already exists
        return
    
    # Create development project
    dev_project = Project(
        id=uuid.uuid4(),
        name="Development Project",
        api_key="dev",
        synced_at=datetime.now(timezone.utc),
    )
    
    db.add(dev_project)
    await db.commit()
    
    print(f"✅ Created development project with API key 'dev' (ID: {dev_project.id})")


async def seed_development_data() -> None:
    """
    Seed all development data.
    
    This function is called during application startup in development environment.
    """
    if not settings.is_development:
        return
    
    async for db in get_db():
        try:
            await seed_development_project(db)
        except Exception as e:
            print(f"❌ Failed to seed development data: {e}")
            raise
        finally:
            await db.close()
        break  # Only need one iteration
