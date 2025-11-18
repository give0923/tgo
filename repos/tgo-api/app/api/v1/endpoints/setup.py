"""Setup endpoints for system initialization."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import generate_api_key, get_password_hash
from app.models import AIProvider, Project, Staff
from app.models.staff import StaffRole, StaffStatus
from app.schemas.setup import (
    ConfigureLLMRequest,
    ConfigureLLMResponse,
    CreateAdminRequest,
    CreateAdminResponse,
    SetupCheckResult,
    SetupStatusResponse,
    VerifySetupResponse,
)
from app.utils.crypto import encrypt_str

logger = get_logger("endpoints.setup")

router = APIRouter()


def _check_system_installed(db: Session) -> tuple[bool, bool, bool]:
    """
    Check if system is installed.
    
    Returns:
        tuple[bool, bool, bool]: (is_installed, has_admin, has_llm_config)
    """
    # Check if any staff exists
    has_admin = db.query(Staff).filter(Staff.deleted_at.is_(None)).first() is not None
    
    # Check if any active AI provider exists
    has_llm_config = (
        db.query(AIProvider)
        .filter(
            AIProvider.deleted_at.is_(None),
            AIProvider.is_active == True
        )
        .first() is not None
    )
    
    is_installed = has_admin and has_llm_config
    
    return is_installed, has_admin, has_llm_config


def _get_setup_completed_time(db: Session) -> Optional[datetime]:
    """Get the timestamp when setup was completed (earliest staff creation time)."""
    first_staff = (
        db.query(Staff)
        .filter(Staff.deleted_at.is_(None))
        .order_by(Staff.created_at.asc())
        .first()
    )
    return first_staff.created_at if first_staff else None


@router.get(
    "/status",
    response_model=SetupStatusResponse,
    summary="Check system installation status",
    description="Check whether the system has completed initial installation and return setup progress."
)
async def get_setup_status(
    db: Session = Depends(get_db),
) -> SetupStatusResponse:
    """
    Check system installation status.
    
    Returns information about whether the system has been set up, including:
    - Whether an admin account exists
    - Whether LLM provider is configured
    - When setup was completed (if applicable)
    """
    is_installed, has_admin, has_llm_config = _check_system_installed(db)
    setup_completed_at = _get_setup_completed_time(db) if is_installed else None
    
    logger.info(
        f"Setup status check: installed={is_installed}, "
        f"has_admin={has_admin}, has_llm={has_llm_config}"
    )
    
    return SetupStatusResponse(
        is_installed=is_installed,
        has_admin=has_admin,
        has_llm_config=has_llm_config,
        setup_completed_at=setup_completed_at,
    )


@router.post(
    "/admin",
    response_model=CreateAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create first admin account",
    description="Create the system's first administrator account and default project. "
                "This endpoint can only be called once during initial setup."
)
async def create_admin(
    admin_data: CreateAdminRequest,
    db: Session = Depends(get_db),
) -> CreateAdminResponse:
    """
    Create the first admin account.
    
    This endpoint:
    1. Checks that no admin exists yet
    2. Creates a default project
    3. Creates the first admin staff member
    4. Returns the created admin information
    
    Can only be called once. Returns 403 if system is already installed.
    """
    # Check if system is already installed
    is_installed, has_admin, _ = _check_system_installed(db)
    
    if has_admin:
        logger.warning("Attempt to create admin when admin already exists")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin already exists. System setup is complete."
        )
    
    # Check username uniqueness
    existing_user = db.query(Staff).filter(
        Staff.username == admin_data.username,
        Staff.deleted_at.is_(None)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{admin_data.username}' already exists"
        )

    # Create default project
    api_key = generate_api_key()
    project = Project(
        name=admin_data.project_name,
        api_key=api_key,
    )
    db.add(project)
    db.flush()  # Get project ID without committing

    logger.info(f"Created default project: {project.name} (ID: {project.id})")

    # Hash password
    password_hash = get_password_hash(admin_data.password)

    # Create admin staff member
    admin = Staff(
        project_id=project.id,
        username=admin_data.username,
        password_hash=password_hash,
        nickname=admin_data.nickname,
        role=StaffRole.USER,  # Admin is a regular user role
        status=StaffStatus.OFFLINE,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.refresh(project)

    logger.info(
        f"Created first admin: {admin.username} (ID: {admin.id}) "
        f"for project {project.name}"
    )

    return CreateAdminResponse(
        id=admin.id,
        username=admin.username,
        nickname=admin.nickname,
        project_id=project.id,
        project_name=project.name,
        created_at=admin.created_at,
    )


@router.post(
    "/llm-config",
    response_model=ConfigureLLMResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Configure LLM provider",
    description="Configure a Large Language Model provider for the system. "
                "Requires that an admin account has been created first."
)
async def configure_llm(
    llm_data: ConfigureLLMRequest,
    db: Session = Depends(get_db),
) -> ConfigureLLMResponse:
    """
    Configure LLM provider.

    This endpoint:
    1. Checks that an admin/project exists
    2. Creates an AIProvider configuration
    3. Encrypts and stores the API key
    4. Returns the configuration details

    The API key is encrypted before storage for security.
    """
    # Check if admin exists (required before LLM config)
    _, has_admin, _ = _check_system_installed(db)

    if not has_admin:
        logger.warning("Attempt to configure LLM before creating admin")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin account must be created before configuring LLM provider"
        )

    # Get the first project (created during admin setup)
    project = db.query(Project).filter(Project.deleted_at.is_(None)).first()

    if not project:
        logger.error("No project found despite admin existing")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System error: No project found"
        )

    # Validate default_model is in available_models if both provided
    if llm_data.default_model and llm_data.available_models:
        if llm_data.default_model not in llm_data.available_models:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="default_model must be in available_models list"
            )

    # Create AI Provider configuration
    ai_provider = AIProvider(
        project_id=project.id,
        provider=llm_data.provider,
        name=llm_data.name,
        api_key=encrypt_str(llm_data.api_key),  # Encrypt API key
        api_base_url=llm_data.api_base_url,
        available_models=llm_data.available_models,
        default_model=llm_data.default_model,
        config=llm_data.config,
        is_active=llm_data.is_active,
    )
    db.add(ai_provider)
    db.commit()
    db.refresh(ai_provider)

    logger.info(
        f"Created LLM provider: {ai_provider.provider}/{ai_provider.name} "
        f"(ID: {ai_provider.id}) for project {project.id}"
    )

    return ConfigureLLMResponse(
        id=ai_provider.id,
        provider=ai_provider.provider,
        name=ai_provider.name,
        default_model=ai_provider.default_model,
        is_active=ai_provider.is_active,
        project_id=ai_provider.project_id,
        created_at=ai_provider.created_at,
    )


@router.get(
    "/verify",
    response_model=VerifySetupResponse,
    summary="Verify installation completeness",
    description="Verify that the system installation is complete and all components are properly configured."
)
async def verify_setup(
    db: Session = Depends(get_db),
) -> VerifySetupResponse:
    """
    Verify installation completeness.

    Performs comprehensive health checks including:
    - Database connectivity
    - Admin account existence
    - LLM provider configuration
    - System readiness

    Returns detailed check results and any errors or warnings found.
    """
    checks = {}
    errors = []
    warnings = []

    # Check 1: Database connection
    try:
        db.execute("SELECT 1")
        checks["database_connected"] = SetupCheckResult(
            passed=True,
            message="Database connection is healthy"
        )
    except Exception as e:
        checks["database_connected"] = SetupCheckResult(
            passed=False,
            message=f"Database connection failed: {str(e)}"
        )
        errors.append(f"Database connection error: {str(e)}")

    # Check 2: Admin exists
    is_installed, has_admin, has_llm_config = _check_system_installed(db)

    if has_admin:
        admin_count = db.query(Staff).filter(Staff.deleted_at.is_(None)).count()
        checks["admin_exists"] = SetupCheckResult(
            passed=True,
            message=f"Admin account exists ({admin_count} staff member(s) found)"
        )
    else:
        checks["admin_exists"] = SetupCheckResult(
            passed=False,
            message="No admin account found"
        )
        errors.append("Admin account has not been created")

    # Check 3: LLM configured
    if has_llm_config:
        llm_count = (
            db.query(AIProvider)
            .filter(
                AIProvider.deleted_at.is_(None),
                AIProvider.is_active == True
            )
            .count()
        )
        checks["llm_configured"] = SetupCheckResult(
            passed=True,
            message=f"LLM provider configured ({llm_count} active provider(s))"
        )
    else:
        checks["llm_configured"] = SetupCheckResult(
            passed=False,
            message="No active LLM provider found"
        )
        errors.append("LLM provider has not been configured")

    # Check 4: Project exists
    project_count = db.query(Project).filter(Project.deleted_at.is_(None)).count()
    if project_count > 0:
        checks["project_exists"] = SetupCheckResult(
            passed=True,
            message=f"Project exists ({project_count} project(s) found)"
        )
    else:
        checks["project_exists"] = SetupCheckResult(
            passed=False,
            message="No project found"
        )
        errors.append("No project has been created")

    # Overall validity
    is_valid = all(check.passed for check in checks.values())

    # Add warnings if partially configured
    if has_admin and not has_llm_config:
        warnings.append("Admin created but LLM provider not configured yet")
    elif has_llm_config and not has_admin:
        warnings.append("LLM provider configured but no admin account exists")

    logger.info(
        f"Setup verification: valid={is_valid}, "
        f"errors={len(errors)}, warnings={len(warnings)}"
    )

    return VerifySetupResponse(
        is_valid=is_valid,
        checks=checks,
        errors=errors,
        warnings=warnings,
    )

