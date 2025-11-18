"""Channel information endpoints."""

from typing import Any, Dict, Optional, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, selectinload
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import get_db
from app.core.security import verify_token
from app.models import Staff, Visitor, VisitorTag, VisitorActivity, Platform
from app.schemas.visitor import (
    VisitorResponse,
    VisitorAIProfileResponse,
    VisitorAIInsightResponse,
    VisitorSystemInfoResponse,
    VisitorActivityResponse,
)
from app.schemas import TagResponse

from app.utils.const import CHANNEL_TYPE_CUSTOMER_SERVICE
from app.utils.encoding import parse_visitor_channel_id
from app.utils.intent import localize_visitor_response_intent


router = APIRouter()


class ChannelInfoResponse(BaseModel):
    name: str = Field(..., description="Channel display name")
    avatar: str = Field(..., description="Channel avatar URL")
    channel_id: str = Field(..., description="WuKongIM channel identifier")
    channel_type: int = Field(..., description="Channel type: 1 (personal), 251 (customer service)")
    entity_type: Literal["visitor", "staff"] = Field(
        ..., description="Entity type represented by this channel: 'visitor' or 'staff'"
    )
    extra: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Scenario 1 – Customer Service Channel (channel_type == 251):\n"
            "- extra contains the complete VisitorResponse as a dictionary. Fields include: id, platform_id, platform_type, "
            "platform_open_id, name, nickname, avatar_url, phone_number, email, company, job_title, source, note, "
            "custom_attributes, created_at, updated_at, deleted_at, first_visit_time, last_visit_time, last_offline_time, "
            "is_online, and any other fields defined by VisitorResponse.\n\n"
            "Scenario 2 – Personal Channel - Staff (channel_type == 1 AND channel_id ends with '-staff'):\n"
            "- extra contains staff metadata as a dictionary with fields: staff_id (UUID string), username (string), role (string, e.g., 'user' or 'agent').\n\n"
            "Scenario 3 – Personal Channel - Visitor (channel_type == 1 AND channel_id does NOT end with '-staff'):\n"
            "- Same as Scenario 1: extra contains the complete VisitorResponse as a dictionary."
        ),
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "platform_id": "00000000-0000-0000-0000-000000000001",
                    "platform_type": "website",
                    "platform_open_id": "visitor_open_id_123",
                    "name": "Jane Doe",
                    "nickname": "jane",
                    "avatar_url": "https://cdn.example.com/avatars/jane.png",
                    "phone_number": "+1-555-0100",
                    "email": "jane@example.com",
                    "company": "Example Inc.",
                    "job_title": "Engineer",
                    "source": "landing_page",
                    "note": "High intent",
                    "custom_attributes": {"plan": "pro"},
                    "created_at": "2024-01-01T12:00:00Z",
                    "updated_at": "2024-01-10T08:30:00Z",
                    "deleted_at": None,
                    "first_visit_time": "2024-01-01T12:00:00Z",
                    "last_visit_time": "2024-01-10T08:00:00Z",
                    "last_offline_time": None,
                    "is_online": True
                },
                {
                    "staff_id": "7b7d3d6e-8a7d-4a23-9a2f-1f1c9c7f8f00",
                    "username": "support.alice",
                    "role": "user"
                },
                {
                    "id": "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
                    "platform_id": "00000000-0000-0000-0000-000000000002",
                    "platform_type": "wechat",
                    "platform_open_id": "wx_abc_987",
                    "name": "John Smith",
                    "nickname": "john",
                    "avatar_url": "https://cdn.example.com/avatars/john.png",
                    "phone_number": None,
                    "email": "john@example.com",
                    "company": None,
                    "job_title": None,
                    "source": "widget",
                    "note": None,
                    "custom_attributes": {},
                    "created_at": "2024-02-02T09:00:00Z",
                    "updated_at": "2024-02-05T09:00:00Z",
                    "deleted_at": None,
                    "first_visit_time": "2024-02-02T09:00:00Z",
                    "last_visit_time": "2024-02-05T09:00:00Z",
                    "last_offline_time": "2024-02-05T09:05:00Z",
                    "is_online": False
                }
            ]
        },
    )


@router.get(
    "/info",
    response_model=ChannelInfoResponse,
    responses={
        200: {
            "description": "Channel info response",
            "content": {
                "application/json": {
                    "examples": {
                        "Customer Service Channel - Visitor": {
                            "summary": "Customer Service Channel - Visitor",
                            "value": {
                                "name": "Jane Doe",
                                "avatar": "https://cdn.example.com/avatars/jane.png",
                                "channel_id": "AbC62xyz",
                                "channel_type": 251,
                                "entity_type": "visitor",
                                "extra": {
                                    "id": "550e8400-e29b-41d4-a716-446655440000",
                                    "platform_id": "00000000-0000-0000-0000-000000000001",
                                    "platform_type": "website",
                                    "platform_open_id": "visitor_open_id_123",
                                    "name": "Jane Doe",
                                    "nickname": "jane",
                                    "avatar_url": "https://cdn.example.com/avatars/jane.png",
                                    "phone_number": "+1-555-0100",
                                    "email": "jane@example.com",
                                    "company": "Example Inc.",
                                    "job_title": "Engineer",
                                    "source": "landing_page",
                                    "note": "High intent",
                                    "custom_attributes": {"plan": "pro"},
                                    "created_at": "2024-01-01T12:00:00Z",
                                    "updated_at": "2024-01-10T08:30:00Z",
                                    "deleted_at": None,
                                    "first_visit_time": "2024-01-01T12:00:00Z",
                                    "last_visit_time": "2024-01-10T08:00:00Z",
                                    "last_offline_time": None,
                                    "is_online": True
                                }
                            }
                        },
                        "Personal Channel - Staff": {
                            "summary": "Personal Channel - Staff",
                            "value": {
                                "name": "Alice Support",
                                "avatar": "https://cdn.example.com/avatars/alice.png",
                                "channel_id": "7b7d3d6e-8a7d-4a23-9a2f-1f1c9c7f8f00-staff",
                                "channel_type": 1,
                                "entity_type": "staff",
                                "extra": {
                                    "staff_id": "7b7d3d6e-8a7d-4a23-9a2f-1f1c9c7f8f00",
                                    "username": "support.alice",
                                    "role": "user"
                                }
                            }
                        },
                        "Personal Channel - Visitor": {
                            "summary": "Personal Channel - Visitor",
                            "value": {
                                "name": "John Smith",
                                "avatar": "https://cdn.example.com/avatars/john.png",
                                "channel_id": "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
                                "channel_type": 1,
                                "entity_type": "visitor",
                                "extra": {
                                    "id": "3f2504e0-4f89-11d3-9a0c-0305e82c3301",
                                    "platform_id": "00000000-0000-0000-0000-000000000002",
                                    "platform_type": "wechat",
                                    "platform_open_id": "wx_abc_987",
                                    "name": "John Smith",
                                    "nickname": "john",
                                    "avatar_url": "https://cdn.example.com/avatars/john.png",
                                    "phone_number": None,
                                    "email": "john@example.com",
                                    "company": None,
                                    "job_title": None,
                                    "source": "widget",
                                    "note": None,
                                    "custom_attributes": {},
                                    "created_at": "2024-02-02T09:00:00Z",
                                    "updated_at": "2024-02-05T09:00:00Z",
                                    "deleted_at": None,
                                    "first_visit_time": "2024-02-02T09:00:00Z",
                                    "last_visit_time": "2024-02-05T09:00:00Z",
                                    "last_offline_time": "2024-02-05T09:05:00Z",
                                    "is_online": False
                                }
                            }
                        }
                    }
                }
            }
        }
    },
)
async def get_channel_info(
    request: Request,
    channel_id: str,
    channel_type: int,
    platform_api_key: Optional[str] = None,
    x_platform_api_key: Optional[str] = Header(None, alias="X-Platform-API-Key"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
) -> ChannelInfoResponse:
    """Retrieve channel information for a given channel_id and channel_type.

    Security:
    - JWT staff: access to channels within the same project (existing behavior)
    - Platform API key: only staff personal channels (channel_type==1 and channel_id endswith '-staff'),
      and only within the same project as the platform
    """
    accept_language = request.headers.get("Accept-Language")

    # Determine authentication method
    current_user: Optional[Staff] = None
    platform: Optional[Platform] = None

    # Try JWT (staff)
    if credentials and credentials.credentials:
        payload = verify_token(credentials.credentials)
        if payload:
            username = payload.get("sub")
            if username:
                current_user = (
                    db.query(Staff)
                    .filter(Staff.username == username, Staff.deleted_at.is_(None))
                    .first()
                )

    # Try Platform API key if no staff user
    if current_user is None:
        api_key = platform_api_key or x_platform_api_key
        if api_key:
            platform = (
                db.query(Platform)
                .filter(Platform.api_key == api_key)
                .first()
            )
            if not platform:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid platform_api_key")
            if platform.deleted_at is not None:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform is deleted")
            if platform.is_active is False:  # noqa: E712
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform is disabled")
        else:
            # Neither JWT nor API key provided
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    # If authenticated via JWT (staff), keep existing behavior
    if current_user is not None:
        # CUSTOMER SERVICE CHANNEL (251): decode Base62 and extract visitor_id
        if channel_type == CHANNEL_TYPE_CUSTOMER_SERVICE:
            try:
                visitor_uuid = parse_visitor_channel_id(channel_id)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid channel_id format")

            visitor = (
                db.query(Visitor)
                .options(
                    selectinload(Visitor.platform),
                    selectinload(Visitor.visitor_tags).selectinload(VisitorTag.tag),
                    selectinload(Visitor.ai_profile),
                    selectinload(Visitor.ai_insight),
                    selectinload(Visitor.system_info),
                )
                .filter(
                    Visitor.id == visitor_uuid,
                    Visitor.project_id == current_user.project_id,
                    Visitor.deleted_at.is_(None),
                )
                .first()
            )
            if not visitor:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitor not found")

            # Build enriched visitor payload (tags, AI profile/insights, system info, recent activities)
            active_tags = [
                vt.tag
                for vt in visitor.visitor_tags
                if vt.deleted_at is None and vt.tag and vt.tag.deleted_at is None
            ]
            tag_responses = [TagResponse.model_validate(tag) for tag in active_tags]

            ai_profile_response = (
                VisitorAIProfileResponse.model_validate(visitor.ai_profile) if visitor.ai_profile else None
            )
            ai_insight_response = (
                VisitorAIInsightResponse.model_validate(visitor.ai_insight) if visitor.ai_insight else None
            )
            system_info_response = (
                VisitorSystemInfoResponse.model_validate(visitor.system_info) if visitor.system_info else None
            )

            recent_activities = (
                db.query(VisitorActivity)
                .filter(
                    VisitorActivity.visitor_id == visitor.id,
                    VisitorActivity.project_id == current_user.project_id,
                    VisitorActivity.deleted_at.is_(None),
                )
                .order_by(VisitorActivity.occurred_at.desc())
                .limit(10)
                .all()
            )
            recent_activity_responses = [
                VisitorActivityResponse.model_validate(activity) for activity in recent_activities
            ]

            visitor_payload = VisitorResponse.model_validate(visitor).model_copy(
                update={
                    "tags": tag_responses,
                    "ai_profile": ai_profile_response,
                    "ai_insights": ai_insight_response,
                    "system_info": system_info_response,
                    "recent_activities": recent_activity_responses,
                }
            )
            localize_visitor_response_intent(visitor_payload, accept_language)

            name = visitor.name or visitor.nickname or "Unknown Visitor"
            avatar = visitor.avatar_url or ""
            return ChannelInfoResponse(
                name=name,
                avatar=avatar,
                channel_id=channel_id,
                channel_type=channel_type,
                entity_type="visitor",
                extra=visitor_payload.model_dump(),
            )

        # PERSONAL CHANNEL (1) with -staff suffix => staff
        if channel_type == 1 and channel_id.endswith("-staff"):
            staff_id_str = channel_id[:-6]
            try:
                staff_uuid = UUID(staff_id_str)
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid staff_id in channel")

            staff = (
                db.query(Staff)
                .filter(
                    Staff.id == staff_uuid,
                    Staff.project_id == current_user.project_id,
                    Staff.deleted_at.is_(None),
                )
                .first()
            )
            if not staff:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

            name = staff.nickname or "Unknown Staff"
            avatar = staff.avatar_url or ""
            extra = {
                "staff_id": str(staff.id),
                "username": staff.username,
                "role": getattr(staff, "role", None),
            }
            return ChannelInfoResponse(
                name=name,
                avatar=avatar,
                channel_id=channel_id,
                channel_type=channel_type,
                entity_type="staff",
                extra=extra,
            )

        # PERSONAL CHANNEL (1) without -staff => visitor
        if channel_type == 1 and not channel_id.endswith("-staff"):
            try:
                visitor_uuid = UUID(channel_id)
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid visitor_id in channel")

            visitor = (
                db.query(Visitor)
                .options(
                    selectinload(Visitor.platform),
                    selectinload(Visitor.visitor_tags).selectinload(VisitorTag.tag),
                    selectinload(Visitor.ai_profile),
                    selectinload(Visitor.ai_insight),
                    selectinload(Visitor.system_info),
                )
                .filter(
                    Visitor.id == visitor_uuid,
                    Visitor.project_id == current_user.project_id,
                    Visitor.deleted_at.is_(None),
                )
                .first()
            )
            if not visitor:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitor not found")

            # Build enriched visitor payload (tags, AI profile/insights, system info, recent activities)
            active_tags = [
                vt.tag
                for vt in visitor.visitor_tags
                if vt.deleted_at is None and vt.tag and vt.tag.deleted_at is None
            ]
            tag_responses = [TagResponse.model_validate(tag) for tag in active_tags]

            ai_profile_response = (
                VisitorAIProfileResponse.model_validate(visitor.ai_profile) if visitor.ai_profile else None
            )
            ai_insight_response = (
                VisitorAIInsightResponse.model_validate(visitor.ai_insight) if visitor.ai_insight else None
            )
            system_info_response = (
                VisitorSystemInfoResponse.model_validate(visitor.system_info) if visitor.system_info else None
            )

            recent_activities = (
                db.query(VisitorActivity)
                .filter(
                    VisitorActivity.visitor_id == visitor.id,
                    VisitorActivity.project_id == current_user.project_id,
                    VisitorActivity.deleted_at.is_(None),
                )
                .order_by(VisitorActivity.occurred_at.desc())
                .limit(10)
                .all()
            )
            recent_activity_responses = [
                VisitorActivityResponse.model_validate(activity) for activity in recent_activities
            ]

            visitor_payload = VisitorResponse.model_validate(visitor).model_copy(
                update={
                    "tags": tag_responses,
                    "ai_profile": ai_profile_response,
                    "ai_insights": ai_insight_response,
                    "system_info": system_info_response,
                    "recent_activities": recent_activity_responses,
                }
            )
            localize_visitor_response_intent(visitor_payload, accept_language)

            name = visitor.name or visitor.nickname or "Unknown Visitor"
            avatar = visitor.avatar_url or ""
            return ChannelInfoResponse(
                name=name,
                avatar=avatar,
                channel_id=channel_id,
                channel_type=channel_type,
                entity_type="visitor",
                extra=visitor_payload.model_dump(),
            )

    # If authenticated via Platform API key, restrict to staff personal channels
    if platform is not None:
        # Only allow channel_type==1 and channel_id ending with '-staff'
        if not (channel_type == 1 and channel_id.endswith("-staff")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only staff personal channels are accessible with platform API key",
            )

        staff_id_str = channel_id[:-6]
        try:
            staff_uuid = UUID(staff_id_str)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid staff_id in channel")

        staff = (
            db.query(Staff)
            .filter(
                Staff.id == staff_uuid,
                Staff.deleted_at.is_(None),
            )
            .first()
        )
        if not staff:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

        # Ensure staff belongs to the same project as the platform
        if staff.project_id != platform.project_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this channel")

        name = staff.nickname or "Unknown Staff"
        avatar = staff.avatar_url or ""
        extra = {
            "staff_id": str(staff.id),
            "username": staff.username,
            "role": getattr(staff, "role", None),
        }
        return ChannelInfoResponse(
            name=name,
            avatar=avatar,
            channel_id=channel_id,
            channel_type=channel_type,
            entity_type="staff",
            extra=extra,
        )

    # Unsupported or unauthorized
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported channel_type")
