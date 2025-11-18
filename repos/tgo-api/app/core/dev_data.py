"""Development data initialization for easier testing and debugging."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import startup_log
from app.core.security import get_password_hash
from app.models.project import Project
from app.models.staff import Staff, StaffRole, StaffStatus

logger = logging.getLogger("app.core.dev_data")

# Development constants
DEV_PROJECT_NAME = "Development Project"
DEV_API_KEY = "dev"
DEV_USERNAME = "dev"
DEV_PASSWORD = "dev"


def get_or_create_dev_project(db: Session) -> Optional[Project]:
    """Get or create the development project."""
    try:
        # Check if dev project already exists
        existing_project = db.query(Project).filter(
            Project.api_key == DEV_API_KEY
        ).first()
        
        if existing_project:
            return existing_project
        
        # Create new development project
        dev_project = Project(
            name=DEV_PROJECT_NAME,
            api_key=DEV_API_KEY
        )
        
        db.add(dev_project)
        db.commit()
        db.refresh(dev_project)

        return dev_project
        
    except Exception as e:
        logger.error(f"❌ Failed to create development project: {e}")
        db.rollback()
        return None


def get_or_create_dev_staff(db: Session, project: Project) -> Optional[Staff]:
    """Get or create the development staff member."""
    try:
        # Check if dev staff already exists
        existing_staff = db.query(Staff).filter(
            Staff.username == DEV_USERNAME,
            Staff.project_id == project.id
        ).first()
        
        if existing_staff:
            return existing_staff
        
        # Create new development staff
        dev_staff = Staff(
            project_id=project.id,
            username=DEV_USERNAME,
            password_hash=get_password_hash(DEV_PASSWORD),
            nickname="Development User",
            role="user",  # Using string value directly
            status="online"  # Using string value directly
        )
        
        db.add(dev_staff)
        db.commit()
        db.refresh(dev_staff)

        return dev_staff
        
    except Exception as e:
        logger.error(f"❌ Failed to create development staff: {e}")
        db.rollback()
        return None


def initialize_development_data() -> bool:
    """Initialize development data if in development environment."""
    if not settings.is_development:
        return False

    startup_log("🔧 Initializing development data...")

    # Create database session
    db = SessionLocal()

    try:
        # Create development project
        dev_project = get_or_create_dev_project(db)
        if not dev_project:
            startup_log("❌ Failed to initialize development project")
            return False

        # Create development staff
        dev_staff = get_or_create_dev_staff(db, dev_project)
        if not dev_staff:
            startup_log("❌ Failed to initialize development staff")
            return False

        startup_log("✅ Development data ready!")
        startup_log("")
        startup_log("🎯 Quick Start Guide:")
        startup_log(f"   📋 API Key: '{DEV_API_KEY}'")
        startup_log(f"   👤 Login: '{DEV_USERNAME}' / '{DEV_PASSWORD}'")
        startup_log(f"   📖 Docs: http://localhost:8000/v1/docs")
        startup_log("")

        return True

    except Exception as e:
        startup_log(f"❌ Development data initialization failed: {e}")
        return False

    finally:
        db.close()


def validate_dev_api_key_security(api_key: str) -> bool:
    """Validate that dev API key is not used in production."""
    if api_key == DEV_API_KEY and not settings.is_development:
        logger.critical(
            f"🚨 SECURITY ALERT: Development API key '{DEV_API_KEY}' used in {settings.ENVIRONMENT} environment! "
            "This is a serious security violation."
        )
        return False
    
    return True


def log_startup_banner() -> None:
    """Log beautiful startup banner."""
    startup_log("╔══════════════════════════════════════════════════════════════╗")
    startup_log("║                    🚀 TGO-Tech API Service                   ║")
    startup_log("║                  Core Business Logic Service                 ║")
    startup_log("╚══════════════════════════════════════════════════════════════╝")
    startup_log("")
    startup_log(f"📦 Version: {settings.PROJECT_VERSION}")
    startup_log(f"🌍 Environment: {settings.ENVIRONMENT.upper()}")
    startup_log("")


def log_development_warnings() -> None:
    """Log development mode warnings."""
    if settings.is_development:
        startup_log("⚠️  DEVELOPMENT MODE ACTIVE", logging.WARNING)
        startup_log("   • Development credentials enabled", logging.WARNING)
        startup_log("   • DO NOT use in production!", logging.WARNING)
        startup_log("")
    else:
        startup_log("🔒 Production mode - development features disabled")
        startup_log("")
