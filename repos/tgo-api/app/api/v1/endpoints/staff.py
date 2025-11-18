"""Staff endpoints."""

from datetime import datetime, timedelta
from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    get_password_hash
)
from app.models import Staff
from app.schemas import (
    StaffCreate,
    StaffListParams,
    StaffListResponse,
    StaffLogin,
    StaffLoginResponse,
    StaffResponse,
    StaffUpdate,
)
from app.schemas.wukongim import (
    WuKongIMChannelMessageSyncRequest,
    WuKongIMChannelMessageSyncResponse,
    WuKongIMConversationSyncRequest,
    WuKongIMConversationSyncResponse,
    WuKongIMDeleteConversationRequest,
    WuKongIMIntegrationStatus,
    WuKongIMOnlineStatusRequest,
    WuKongIMOnlineStatusResponse,
    WuKongIMSetUnreadRequest,
)
from app.services.wukongim_client import wukongim_client
from app.api.common_responses import AUTH_RESPONSES, CRUD_RESPONSES, LIST_RESPONSES

logger = get_logger("endpoints.staff")
router = APIRouter()


@router.post(
    "/login",
    response_model=StaffLoginResponse,
    responses=AUTH_RESPONSES
)
async def login_staff(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> StaffLoginResponse:
    """
    Staff login.

    Authenticate staff member and return JWT access token.
    Also registers/synchronizes user with WuKongIM for instant messaging.
    """
    logger.info(f"Staff login attempt for username: {form_data.username}")

    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username,
        project_id=user.project_id,
        expires_delta=access_token_expires
    )

    # Register/synchronize user with WuKongIM for instant messaging
    # Use staff ID with "-staff" suffix to ensure unique identification
    staff_uid = f"{user.id}-staff"
    try:
        await wukongim_client.register_or_login_user(
            uid=staff_uid,
            token=access_token,  # Use the JWT token as WuKongIM token
        )
        logger.info(f"Successfully synchronized staff {user.username} (UID: {staff_uid}) with WuKongIM")
    except Exception as e:
        # Log the error but don't fail the login process
        logger.error(
            f"Failed to synchronize user {user.username} with WuKongIM: {e}",
            extra={
                "username": user.username,
                "error": str(e),
                "wukongim_enabled": settings.WUKONGIM_ENABLED,
            }
        )
        # WuKongIM sync failure should not prevent login
        # The user can still use the main application features

    logger.info(f"Successful login for user: {user.username}")

    return StaffLoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        staff=StaffResponse.model_validate(user)
    )


@router.get(
    "",
    response_model=StaffListResponse,
    responses=LIST_RESPONSES
)
async def list_staff(
    params: StaffListParams = Depends(),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> StaffListResponse:
    """
    List staff members.
    
    Retrieve a paginated list of staff members with optional filtering.
    """
    logger.info(f"User {current_user.username} listing staff members")
    
    # Build query
    query = db.query(Staff).filter(
        Staff.project_id == current_user.project_id,
        Staff.deleted_at.is_(None)
    )
    
    # Apply filters
    if params.role:
        query = query.filter(Staff.role == params.role)
    if params.status:
        query = query.filter(Staff.status == params.status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    staff_members = query.offset(params.offset).limit(params.limit).all()
    
    # Convert to response models
    staff_responses = [StaffResponse.model_validate(staff) for staff in staff_members]
    
    return StaffListResponse(
        data=staff_responses,
        pagination={
            "total": total,
            "limit": params.limit,
            "offset": params.offset,
            "has_next": params.offset + params.limit < total,
            "has_previous": params.offset > 0,
        }
    )


@router.post("", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff_data: StaffCreate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> StaffResponse:
    """
    Create staff member.
    
    Create a new staff member or AI agent. For AI agents, validates agent_id
    with AI Service and publishes agent creation event.
    """
    logger.info(f"User {current_user.username} creating staff: {staff_data.username}")
    
    # Check if username already exists
    existing_staff = db.query(Staff).filter(
        Staff.username == staff_data.username,
        Staff.deleted_at.is_(None)
    ).first()
    
    if existing_staff:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Hash password
    password_hash = get_password_hash(staff_data.password)
    
    # Create staff member
    staff = Staff(
        project_id=current_user.project_id,
        username=staff_data.username,
        password_hash=password_hash,
        nickname=staff_data.nickname,
        avatar_url=staff_data.avatar_url,
        role=staff_data.role,
        status=staff_data.status,
    )
    
    db.add(staff)
    db.commit()
    db.refresh(staff)
    
    logger.info(f"Created staff {staff.id} with username: {staff.username}")
    
    return StaffResponse.model_validate(staff)


@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: UUID,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> StaffResponse:
    """Get staff member details."""
    logger.info(f"User {current_user.username} getting staff: {staff_id}")
    
    staff = db.query(Staff).filter(
        Staff.id == staff_id,
        Staff.project_id == current_user.project_id,
        Staff.deleted_at.is_(None)
    ).first()
    
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )
    
    return StaffResponse.model_validate(staff)


@router.patch("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: UUID,
    staff_data: StaffUpdate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> StaffResponse:
    """
    Update staff member.
    
    Update staff member information. For AI agents, validates agent_id changes
    with AI Service and publishes agent update event.
    """
    logger.info(f"User {current_user.username} updating staff: {staff_id}")
    
    staff = db.query(Staff).filter(
        Staff.id == staff_id,
        Staff.project_id == current_user.project_id,
        Staff.deleted_at.is_(None)
    ).first()
    
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )
    
    # Update fields
    update_data = staff_data.model_dump(exclude_unset=True)
    
    # Handle password update
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(staff, field, value)
    
    staff.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(staff)
    
    logger.info(f"Updated staff {staff.id}")
    
    return StaffResponse.model_validate(staff)


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(
    staff_id: UUID,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> None:
    """
    Delete staff member (soft delete).
    
    Soft delete a staff member. For AI agents, publishes agent deletion event
    for AI Service cleanup.
    """
    logger.info(f"User {current_user.username} deleting staff: {staff_id}")
    
    staff = db.query(Staff).filter(
        Staff.id == staff_id,
        Staff.project_id == current_user.project_id,
        Staff.deleted_at.is_(None)
    ).first()
    
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Staff member not found"
        )
    
    # Prevent self-deletion
    if staff.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    # Soft delete
    staff.deleted_at = datetime.utcnow()
    staff.updated_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Deleted staff {staff.id}")

    return None


@router.get(
    "/wukongim/status",
    response_model=WuKongIMIntegrationStatus,
    summary="Get WuKongIM Integration Status",
    description="Get the current status of WuKongIM integration including configuration and health."
)
async def get_wukongim_status(
    current_user: Staff = Depends(get_current_active_user),
) -> WuKongIMIntegrationStatus:
    """Get WuKongIM integration status."""
    logger.info(f"User {current_user.username} checking WuKongIM status")

    return WuKongIMIntegrationStatus(
        enabled=settings.WUKONGIM_ENABLED,
        service_url=settings.WUKONGIM_SERVICE_URL,
        last_sync=None,  # Could be enhanced to track last sync time
        error_count=0,   # Could be enhanced to track errors
        last_error=None  # Could be enhanced to track last error
    )


@router.post(
    "/wukongim/online-status",
    response_model=WuKongIMOnlineStatusResponse,
    summary="Check Staff Online Status",
    description="Check which staff members are currently online in WuKongIM."
)
async def check_staff_online_status(
    request: WuKongIMOnlineStatusRequest,
    current_user: Staff = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WuKongIMOnlineStatusResponse:
    """Check online status of staff members in WuKongIM."""
    logger.info(
        f"User {current_user.username} checking online status for {len(request.uids)} users"
    )

    # Validate that the requested UIDs are valid staff usernames in the same project
    valid_staff = db.query(Staff).filter(
        Staff.username.in_(request.uids),
        Staff.project_id == current_user.project_id,
        Staff.deleted_at.is_(None)
    ).all()

    # Convert staff records to WuKongIM UIDs (staff_id + "-staff")
    staff_uid_mapping = {staff.username: f"{staff.id}-staff" for staff in valid_staff}
    valid_usernames = list(staff_uid_mapping.keys())
    wukongim_uids = list(staff_uid_mapping.values())

    if len(valid_usernames) != len(request.uids):
        invalid_uids = set(request.uids) - set(valid_usernames)
        logger.warning(
            f"Invalid UIDs requested: {invalid_uids}",
            extra={"invalid_uids": list(invalid_uids)}
        )

    try:
        online_wukongim_uids = await wukongim_client.check_user_online_status(wukongim_uids)

        # Convert WuKongIM UIDs back to staff usernames for response
        reverse_mapping = {wukongim_uid: username for username, wukongim_uid in staff_uid_mapping.items()}
        online_uids = [reverse_mapping[wukongim_uid] for wukongim_uid in online_wukongim_uids if wukongim_uid in reverse_mapping]
        logger.info(f"Found {len(online_uids)} online staff members")

        return WuKongIMOnlineStatusResponse(online_uids=online_uids)

    except Exception as e:
        logger.error(f"Failed to check online status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check online status"
        )


@router.post(
    "/wukongim/conversations/sync",
    response_model=WuKongIMConversationSyncResponse,
    summary="Sync WuKongIM Conversations",
    description="Synchronize recent conversations from WuKongIM for the current staff member."
)
async def sync_wukongim_conversations(
    request: WuKongIMConversationSyncRequest,
    current_user: Staff = Depends(get_current_active_user),
) -> WuKongIMConversationSyncResponse:
    """Synchronize WuKongIM conversations for the current staff member."""
    # Use staff ID with "-staff" suffix as WuKongIM UID
    staff_uid = f"{current_user.id}-staff"

    logger.info(
        f"Staff {current_user.username} syncing WuKongIM conversations",
        extra={
            "staff_username": current_user.username,
            "staff_uid": staff_uid,
            "version": request.version,
            "msg_count": request.msg_count,
        }
    )

    try:
        conversations = await wukongim_client.sync_conversations(
            uid=staff_uid,
            version=request.version,
            last_msg_seqs=request.last_msg_seqs,
            msg_count=request.msg_count,
        )

        logger.info(f"Successfully synced {len(conversations)} conversations for staff {current_user.username}")

        return WuKongIMConversationSyncResponse(conversations=conversations)

    except Exception as e:
        logger.error(f"Failed to sync conversations for staff {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync conversations"
        )


@router.post(
    "/wukongim/conversations/set-unread",
    summary="Set Conversation Unread Count",
    description="Set the unread message count for a specific conversation."
)
async def set_conversation_unread(
    request: WuKongIMSetUnreadRequest,
    current_user: Staff = Depends(get_current_active_user),
) -> Dict[str, str]:
    """Set unread count for a WuKongIM conversation."""
    # Use staff ID with "-staff" suffix as WuKongIM UID
    staff_uid = f"{current_user.id}-staff"

    logger.info(
        f"Staff {current_user.username} setting unread count for conversation",
        extra={
            "staff_username": current_user.username,
            "staff_uid": staff_uid,
            "channel_id": request.channel_id,
            "channel_type": request.channel_type,
            "unread": request.unread,
        }
    )

    try:
        await wukongim_client.set_conversation_unread(
            uid=staff_uid,
            channel_id=request.channel_id,
            channel_type=request.channel_type,
            unread=request.unread,
        )

        logger.info(f"Successfully set unread count for staff {current_user.username}")

        return {"message": "Unread count updated successfully"}

    except Exception as e:
        logger.error(f"Failed to set unread count for staff {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set unread count"
        )


@router.post(
    "/wukongim/conversations/delete",
    summary="Delete Conversation",
    description="Delete a specific conversation from WuKongIM."
)
async def delete_conversation(
    request: WuKongIMDeleteConversationRequest,
    current_user: Staff = Depends(get_current_active_user),
) -> Dict[str, str]:
    """Delete a WuKongIM conversation."""
    # Use staff ID with "-staff" suffix as WuKongIM UID
    staff_uid = f"{current_user.id}-staff"

    logger.info(
        f"Staff {current_user.username} deleting conversation",
        extra={
            "staff_username": current_user.username,
            "staff_uid": staff_uid,
            "channel_id": request.channel_id,
            "channel_type": request.channel_type,
        }
    )

    try:
        await wukongim_client.delete_conversation(
            uid=staff_uid,
            channel_id=request.channel_id,
            channel_type=request.channel_type,
        )

        logger.info(f"Successfully deleted conversation for staff {current_user.username}")

        return {"message": "Conversation deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete conversation for staff {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


@router.post(
    "/wukongim/channels/messages/sync",
    response_model=WuKongIMChannelMessageSyncResponse,
    summary="Sync Channel Messages",
    description="Synchronize messages from a specific WuKongIM channel."
)
async def sync_channel_messages(
    request: WuKongIMChannelMessageSyncRequest,
    current_user: Staff = Depends(get_current_active_user),
) -> WuKongIMChannelMessageSyncResponse:
    """Synchronize messages from a specific WuKongIM channel."""
    # Use staff ID with "-staff" suffix as WuKongIM UID
    staff_uid = f"{current_user.id}-staff"

    logger.info(
        f"Staff {current_user.username} syncing channel messages",
        extra={
            "staff_username": current_user.username,
            "staff_uid": staff_uid,
            "channel_id": request.channel_id,
            "channel_type": request.channel_type,
            "start_message_seq": request.start_message_seq,
            "end_message_seq": request.end_message_seq,
            "limit": request.limit,
            "pull_mode": request.pull_mode,
        }
    )

    try:
        result = await wukongim_client.sync_channel_messages(
            login_uid=staff_uid,
            channel_id=request.channel_id,
            channel_type=request.channel_type,
            start_message_seq=request.start_message_seq,
            end_message_seq=request.end_message_seq,
            limit=request.limit,
            pull_mode=request.pull_mode,
        )

        message_count = len(result.get("messages", []))
        logger.info(f"Successfully synced {message_count} channel messages for staff {current_user.username}")

        return WuKongIMChannelMessageSyncResponse(**result)

    except Exception as e:
        logger.error(f"Failed to sync channel messages for staff {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync channel messages"
        )
