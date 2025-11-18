from __future__ import annotations

import asyncio
import json
import time
from urllib.parse import quote
import unicodedata
# import base64  # replaced by Base62 utility
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.responses import StreamingResponse, FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.platform import Platform
from app.models.visitor import Visitor
from app.models import ChannelMember
from app.services.kafka_producer import publish_incoming_message
from app.services import platform_stream_bus
from app.utils.const import CHANNEL_TYPE_CUSTOMER_SERVICE, MEMBER_TYPE_STAFF
from app.utils.encoding import build_visitor_channel_id, parse_visitor_channel_id
from app.schemas.messages import IncomingMessagePayload
# Import visitor creation helper from visitors endpoint
from app.api.v1.endpoints.visitors import _create_visitor_with_channel
from app.schemas.chat import (
    OpenAIChatCompletionRequest,
    OpenAIChatCompletionResponse,
    OpenAIChatCompletionChoice,
    OpenAIChatCompletionUsage,
    OpenAIChatMessage,
    OpenAIChatCompletionChunk,
    OpenAIChatCompletionChunkChoice,
    OpenAIChatCompletionDelta,
)


router = APIRouter()


class ChatCompletionRequest(BaseModel):
    """Request payload for streaming chat completion.

    Notes:
    - api_key refers to the Platform API key used by the client integration
    - from_uid identifies the end-user on the client platform
    - message is the chat input to be completed by AI
    - timeout_seconds bounds the SSE stream duration
    """
    api_key: str
    message: str
    from_uid: str
    extra: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = 120
    channel_id: Optional[str] = None
    channel_type: Optional[int] = None
    system_message: Optional[str] = Field(
        None, description="System message/prompt to guide the AI agent"
    )
    expected_output: Optional[str] = Field(
        None, description="Expected output format or description for the AI agent"
    )



def _sse_format(event: Dict[str, Any]) -> str:
    event_type = event.get("event_type") or "message"
    data = json.dumps(event, ensure_ascii=False)
    return f"event: {event_type}\ndata: {data}\n\n"


# ============================================================================
# Helper Functions for Code Reuse
# ============================================================================

def _validate_platform_and_project(
    platform_api_key: str,
    db: Session
) -> tuple[Platform, Any]:
    """Validate Platform API key and return platform with project.

    Args:
        platform_api_key: The Platform API key to validate
        db: Database session

    Returns:
        tuple[Platform, Project]: Validated platform and its project

    Raises:
        HTTPException: If API key is invalid or platform has no project
    """
    platform: Optional[Platform] = (
        db.query(Platform)
        .filter(
            Platform.api_key == platform_api_key,
            Platform.is_active == True,  # noqa: E712
            Platform.deleted_at.is_(None),
        )
        .first()
    )
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    project = platform.project
    if not project or not project.api_key:
        raise HTTPException(
            status_code=400,
            detail="Platform is not linked to a valid project"
        )

    return platform, project


def _check_ai_disabled(
    platform: Platform,
    visitor: Optional[Visitor]
) -> bool:
    """Check if AI is disabled for the platform or visitor.

    Args:
        platform: The platform object
        visitor: The visitor object (optional)

    Returns:
        bool: True if AI is disabled, False otherwise
    """
    if getattr(platform, "ai_disabled", False):
        return True
    if visitor and getattr(visitor, "ai_disabled", False):
        return True
    return False


def _get_staff_info(
    channel_id: str,
    db: Session
) -> tuple[Optional[str], Optional[str]]:
    """Get staff information for a channel.

    Args:
        channel_id: The channel ID
        db: Database session

    Returns:
        tuple[Optional[str], Optional[str]]: (staff_id, staff_cid)
    """
    try:
        cm = (
            db.query(ChannelMember)
            .filter(
                ChannelMember.channel_id == channel_id,
                ChannelMember.member_type == MEMBER_TYPE_STAFF,
                ChannelMember.deleted_at.is_(None),
            )
            .first()
        )
        if cm:
            staff_id = str(cm.member_id)
            staff_cid = f"{staff_id}-staff"
            return staff_id, staff_cid
    except Exception:
        pass

    return None, None


async def _publish_and_subscribe(
    payload: IncomingMessagePayload,
    client_msg_no: str
) -> tuple[asyncio.Queue, Any]:
    """Publish message to Kafka and subscribe to response stream.

    Args:
        payload: The message payload to publish
        client_msg_no: The client message number for correlation

    Returns:
        tuple[asyncio.Queue, Callable]: (event_queue, unsubscribe_function)

    Raises:
        HTTPException: If message publishing fails
    """
    # Subscribe to response stream
    queue, unsubscribe = await platform_stream_bus.subscribe(client_msg_no)

    # Publish message
    ok = await publish_incoming_message(payload)
    if not ok:
        unsubscribe()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish message"
        )

    return queue, unsubscribe


async def _collect_completion_from_stream(
    queue: asyncio.Queue,
    timeout_seconds: int
) -> str:
    """Collect completion text from event stream.

    Args:
        queue: The event queue to read from
        timeout_seconds: Maximum time to wait for completion

    Returns:
        str: The collected completion text

    Raises:
        HTTPException: If timeout occurs or error event is received
    """
    completion_text = ""
    deadline = time.monotonic() + timeout_seconds

    while True:
        timeout_left = deadline - time.monotonic()
        if timeout_left <= 0:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI response timeout"
            )

        try:
            event = await asyncio.wait_for(queue.get(), timeout=timeout_left)
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI response timeout"
            )

        # Process event
        if isinstance(event, dict):
            event_type = event.get("event_type")

            # Collect text tokens
            if event_type == "team_run_content":
                data = event.get("data", {})
                content = data.get("content", "")
                completion_text += content

            # Check for completion
            elif event_type == "workflow_completed":
                break

            # Handle errors
            elif event_type == "error":
                error_msg = event.get("data", {}).get("message", "Unknown error")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI processing error: {error_msg}"
                )

    return completion_text


def _extract_messages_from_openai_format(
    messages: list[OpenAIChatMessage],
    user_field: Optional[str] = None
) -> tuple[str, Optional[str], str]:
    """Extract user message, system message, and platform_open_id from OpenAI message format.

    Args:
        messages: List of OpenAI chat messages
        user_field: Optional user identifier from request (platform_open_id)

    Returns:
        tuple[str, Optional[str], str]: (user_message, system_message, platform_open_id)

    Raises:
        HTTPException: If no user message is found
    """
    user_message = None
    system_message = None

    for msg in reversed(messages):
        if msg.role == "user" and user_message is None:
            user_message = msg.content
        elif msg.role == "system" and system_message is None:
            system_message = msg.content

    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user message found in messages array"
        )

    # Use the 'user' field from request as platform_open_id, or generate a default
    platform_open_id = user_field or f"openai_user_{uuid4().hex[:8]}"

    return user_message, system_message, platform_open_id


def _estimate_token_usage(
    messages: list[OpenAIChatMessage],
    completion_text: str
) -> tuple[int, int, int]:
    """Estimate token usage for prompt and completion.

    This is a rough approximation. In production, you should get
    actual token counts from the AI service.

    Args:
        messages: List of OpenAI chat messages
        completion_text: The completion text

    Returns:
        tuple[int, int, int]: (prompt_tokens, completion_tokens, total_tokens)
    """
    prompt_text = " ".join([msg.content for msg in messages])
    prompt_tokens = len(prompt_text.split())  # Rough estimate
    completion_tokens = len(completion_text.split())  # Rough estimate
    total_tokens = prompt_tokens + completion_tokens

    return prompt_tokens, completion_tokens, total_tokens


def _build_openai_completion_response(
    completion_id: str,
    created_timestamp: int,
    model: str,
    completion_text: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int
) -> OpenAIChatCompletionResponse:
    """Build OpenAI-compatible completion response.

    Args:
        completion_id: Unique completion ID
        created_timestamp: Unix timestamp
        model: Model name
        completion_text: The completion text
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        total_tokens: Total number of tokens

    Returns:
        OpenAIChatCompletionResponse: The formatted response
    """
    return OpenAIChatCompletionResponse(
        id=completion_id,
        object="chat.completion",
        created=created_timestamp,
        model=model,
        choices=[
            OpenAIChatCompletionChoice(
                index=0,
                message=OpenAIChatMessage(
                    role="assistant",
                    content=completion_text,
                ),
                finish_reason="stop",
            )
        ],
        usage=OpenAIChatCompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        ),
    )


async def _generate_openai_stream_chunks(
    queue: asyncio.Queue,
    unsubscribe: Any,
    completion_id: str,
    created_timestamp: int,
    model: str,
    timeout_seconds: int = 120
):
    """Generate OpenAI-compatible streaming chunks from event queue.

    This async generator yields SSE-formatted chunks compatible with
    OpenAI's streaming response format.

    Args:
        queue: The event queue to read from
        unsubscribe: Function to call when done
        completion_id: Unique completion ID
        created_timestamp: Unix timestamp
        model: Model name
        timeout_seconds: Maximum time to wait for completion

    Yields:
        str: SSE-formatted chunk strings
    """
    try:
        # Send initial chunk with role
        initial_chunk = OpenAIChatCompletionChunk(
            id=completion_id,
            object="chat.completion.chunk",
            created=created_timestamp,
            model=model,
            choices=[
                OpenAIChatCompletionChunkChoice(
                    index=0,
                    delta=OpenAIChatCompletionDelta(role="assistant", content=""),
                    finish_reason=None,
                )
            ],
        )
        yield f"data: {initial_chunk.model_dump_json()}\n\n"

        # Stream tokens
        deadline = time.monotonic() + timeout_seconds

        while True:
            timeout_left = deadline - time.monotonic()
            if timeout_left <= 0:
                break

            try:
                event = await asyncio.wait_for(queue.get(), timeout=timeout_left)
            except asyncio.TimeoutError:
                break

            if isinstance(event, dict):
                event_type = event.get("event_type")

                # Stream text tokens
                if event_type == "team_run_content":
                    data = event.get("data", {})
                    content = data.get("content", "")
                    if content:
                        chunk = OpenAIChatCompletionChunk(
                            id=completion_id,
                            object="chat.completion.chunk",
                            created=created_timestamp,
                            model=model,
                            choices=[
                                OpenAIChatCompletionChunkChoice(
                                    index=0,
                                    delta=OpenAIChatCompletionDelta(content=content),
                                    finish_reason=None,
                                )
                            ],
                        )
                        yield f"data: {chunk.model_dump_json()}\n\n"

                # Check for completion
                elif event_type == "workflow_completed":
                    # Send final chunk with finish_reason
                    final_chunk = OpenAIChatCompletionChunk(
                        id=completion_id,
                        object="chat.completion.chunk",
                        created=created_timestamp,
                        model=model,
                        choices=[
                            OpenAIChatCompletionChunkChoice(
                                index=0,
                                delta=OpenAIChatCompletionDelta(),
                                finish_reason="stop",
                            )
                        ],
                    )
                    yield f"data: {final_chunk.model_dump_json()}\n\n"
                    break

                # Handle errors
                elif event_type == "error":
                    error_chunk = OpenAIChatCompletionChunk(
                        id=completion_id,
                        object="chat.completion.chunk",
                        created=created_timestamp,
                        model=model,
                        choices=[
                            OpenAIChatCompletionChunkChoice(
                                index=0,
                                delta=OpenAIChatCompletionDelta(),
                                finish_reason="error",
                            )
                        ],
                    )
                    yield f"data: {error_chunk.model_dump_json()}\n\n"
                    break

        # Send [DONE] marker
        yield "data: [DONE]\n\n"

    except asyncio.CancelledError:
        raise
    finally:
        unsubscribe()


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/completion", summary="Stream chat completion responses", tags=["Chat"])
async def chat_completion(req: ChatCompletionRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    """Streaming chat completion endpoint.

    - Auth: Platform API key in request payload (api_key)
    - Behavior: Publishes message to Kafka and streams AI events over SSE
    - Output: Server-Sent Events (SSE) with tokens and a final complete event
    """
    # 1) Validate Platform API key and get project
    platform, project = _validate_platform_and_project(req.api_key, db)

    # 2) Query visitor by platform_open_id (req.from_uid is platform_open_id, not visitor_id)
    visitor = (
        db.query(Visitor)
        .filter(
            Visitor.platform_id == platform.id,
            Visitor.platform_open_id == req.from_uid,  # from_uid is platform_open_id
            Visitor.deleted_at.is_(None),
        )
        .first()
    )

    # 3) Prepare correlation and session IDs
    client_msg_no = f"plat_{uuid4().hex}"

    # Resolve channel_id (use provided value or build from visitor_id)
    if req.channel_id:
        channel_id_enc = req.channel_id
    else:
        # If visitor exists, use visitor.id to build channel_id
        # Otherwise, use platform_open_id as fallback (for backward compatibility)
        if visitor:
            channel_id_enc = build_visitor_channel_id(visitor.id)
        else:
            # Fallback: use platform_open_id directly (may not be a valid UUID)
            channel_id_enc = build_visitor_channel_id(req.from_uid)

    # Resolve channel_type (default to 251)
    channel_type = req.channel_type if req.channel_type is not None else CHANNEL_TYPE_CUSTOMER_SERVICE

    session_id = f"{channel_id_enc}@{channel_type}"

    # 4) Check AI disabled status
    ai_disabled = _check_ai_disabled(platform, visitor)

    # 5) Get staff info if available
    if visitor:
        print("visitor: %s", visitor.id, visitor.ai_disabled)
    staff_id, staff_cid = _get_staff_info(channel_id_enc, db)

    # 6) Build payload (use visitor_id as from_uid)
    payload = IncomingMessagePayload(
        from_uid=req.from_uid,  # This is  visitor_id, not platform_open_id
        channel_id=channel_id_enc,
        channel_type=channel_type,
        platform_id=str(platform.id),
        platform_type=platform.type,
        message_text=req.message,
        project_id=str(platform.project_id),
        project_api_key=project.api_key,
        client_msg_no=client_msg_no,
        session_id=session_id,
        received_at=int(time.time() * 1000),
        source="platform_sse",
        extra=req.extra or {},
        staff_id=staff_id,
        staff_cid=staff_cid,
        system_message=req.system_message,
        expected_output=req.expected_output,
        ai_disabled=ai_disabled,
    )

    # 6) Conditional AI processing behavior
    if ai_disabled:
        # Publish for tracking/logging, but do not subscribe or stream AI events
        ok = await publish_incoming_message(payload)
        async def disabled_gen():
            if not ok:
                yield _sse_format({"event_type": "error", "data": {"message": "failed to publish message"}})
            else:
                yield _sse_format({
                    "event_type": "ai_disabled",
                    "data": {"message": "AI responses are disabled for this visitor/platform"},
                })
        return StreamingResponse(disabled_gen(), media_type="text/event-stream")

    # 7) AI is enabled: subscribe then publish and stream
    queue, unsubscribe = await platform_stream_bus.subscribe(client_msg_no)

    async def event_generator() -> Any:
        try:
            deadline = time.monotonic() + float(req.timeout_seconds or 120)
            while True:
                timeout_left = deadline - time.monotonic()
                if timeout_left <= 0:
                    yield _sse_format({"event_type": "timeout", "data": {"message": "stream timeout"}})
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=timeout_left)
                except asyncio.TimeoutError:
                    yield _sse_format({"event_type": "timeout", "data": {"message": "stream timeout"}})
                    break

                yield _sse_format(event)

                if isinstance(event, dict) and event.get("event_type") == "workflow_completed":
                    break
        except asyncio.CancelledError:
            raise
        finally:
            unsubscribe()

    ok = await publish_incoming_message(payload)
    if not ok:
        async def error_gen():
            yield _sse_format({"event_type": "error", "data": {"message": "failed to publish message"}})
        return StreamingResponse(error_gen(), media_type="text/event-stream")

    return StreamingResponse(event_generator(), media_type="text/event-stream")




from typing import Optional as _Optional
from fastapi import UploadFile, File, Form, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
from app.core.security import get_current_active_user, verify_token
from app.models import Platform, Staff, Visitor, ChatFile
from app.schemas import ChatFileUploadResponse, StaffSendPlatformMessageRequest
from uuid import UUID
from pathlib import Path
import os
import re
import secrets
import mimetypes


@router.post(
    "/messages/send",
    tags=["Chat"],
    summary="Send message via platform service",
    description=(
        "Forward a staff-authenticated outbound message to the Platform Service "
        "(`/v1/messages/send`). This endpoint enriches the payload with the platform API key "
        "and staff identifier and returns the Platform Service response."
    ),
)
async def staff_send_platform_message(
    req: StaffSendPlatformMessageRequest,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_active_user),
) -> Response:
    if req.channel_type != CHANNEL_TYPE_CUSTOMER_SERVICE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only customer service channels (type 251) are supported",
        )

    try:
        visitor_uuid = parse_visitor_channel_id(req.channel_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid channel_id format")

    membership = (
        db.query(ChannelMember)
        .filter(
            ChannelMember.channel_id == req.channel_id,
            ChannelMember.channel_type == req.channel_type,
            ChannelMember.member_id == current_user.id,
            ChannelMember.member_type == MEMBER_TYPE_STAFF,
            ChannelMember.deleted_at.is_(None),
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff not assigned to this channel")

    visitor = (
        db.query(Visitor)
        .options(joinedload(Visitor.platform))
        .filter(
            Visitor.id == visitor_uuid,
            Visitor.project_id == current_user.project_id,
            Visitor.deleted_at.is_(None),
        )
        .first()
    )
    if not visitor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitor not found")

    platform = visitor.platform
    if not platform or platform.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Visitor platform is unavailable")
    if not platform.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Visitor platform is disabled")
    if not platform.api_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Platform API key is missing")
    if platform.project_id != current_user.project_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for visitor platform")

    target_url = f"{settings.PLATFORM_SERVICE_URL.rstrip('/')}/v1/messages/send"
    outbound_payload: Dict[str, Any] = {
        "platform_api_key": platform.api_key,
        "from_uid": f"{current_user.id}-staff",
        "platform_open_id": visitor.platform_open_id,
        "channel_id": req.channel_id,
        "channel_type": req.channel_type,
        "payload": req.payload,
        "client_msg_no": req.client_msg_no or f"staff_{uuid4().hex}",
    }

    headers = {"Content-Type": "application/json"}
    if settings.PLATFORM_SERVICE_API_KEY:
        headers["Authorization"] = f"Bearer {settings.PLATFORM_SERVICE_API_KEY}"

    try:
        async with httpx.AsyncClient(timeout=settings.PLATFORM_SERVICE_TIMEOUT) as client:
            resp = await client.post(target_url, json=outbound_payload, headers=headers)
    except httpx.TimeoutException:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Platform Service timeout")
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Platform Service request error: {exc}",
        )

    hop_by_hop = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-length",
    }
    passthrough_headers = {k: v for k, v in resp.headers.items() if k.lower() not in hop_by_hop}
    media_type = resp.headers.get("content-type")
    return Response(content=resp.content, status_code=resp.status_code, headers=passthrough_headers, media_type=media_type)


def _sanitize_filename(name: str, limit: int = 100) -> str:
    name = name.replace("\\", "_").replace("/", "_").replace("..", ".")
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    if len(name) <= limit:
        return name
    # Preserve extension if present
    if "." in name:
        base, ext = name.rsplit(".", 1)
        base = base[: max(1, limit - len(ext) - 1)]
        return f"{base}.{ext}"
    return name[:limit]


@router.post("/upload", response_model=ChatFileUploadResponse, tags=["Chat"])
async def chat_file_upload(
    file: UploadFile = File(...),
    channel_id: str = Form(...),
    channel_type: int = Form(...),
    platform_api_key: _Optional[str] = Form(None),
    x_platform_api_key: _Optional[str] = Header(None, alias="X-Platform-API-Key"),
    credentials: _Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
):
    """Upload a file for a chat channel with dual authentication support."""
    # 1) Authenticate: JWT staff or platform_api_key
    current_user: _Optional[Staff] = None
    platform: _Optional[Platform] = None

    if credentials and credentials.credentials:
        payload = verify_token(credentials.credentials)
        if payload:
            username = payload.get("sub")
            if username:
                current_user = db.query(Staff).filter(Staff.username == username, Staff.deleted_at.is_(None)).first()
    plat_key = platform_api_key or x_platform_api_key
    if not current_user and plat_key:
        platform = (
            db.query(Platform)
            .filter(Platform.api_key == plat_key, Platform.is_active == True, Platform.deleted_at.is_(None))
            .first()
        )
    if not current_user and not platform:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    # Determine project context
    if current_user:
        project_id = current_user.project_id
        uploaded_by = current_user.username
    else:
        assert platform is not None
        project_id = platform.project_id
        uploaded_by = "visitor"

    # 2) Access validation by channel
    if channel_type == CHANNEL_TYPE_CUSTOMER_SERVICE:
        try:
            visitor_uuid = parse_visitor_channel_id(channel_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid channel_id format")

        visitor = (
            db.query(Visitor)
            .filter(Visitor.id == visitor_uuid, Visitor.deleted_at.is_(None))
            .first()
        )
        if not visitor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitor not found")

        if platform:
            if visitor.platform_id != platform.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform not authorized for channel")
        else:
            if visitor.project_id != project_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to channel")

    elif channel_type == 1:
        # Personal channel: either visitor UUID or staff-suffixed id
        if channel_id.endswith("-staff"):
            # Only allowed for the staff owner (JWT path)
            if not current_user:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform cannot upload to staff channel")
            staff_id_str = channel_id[:-6]
            try:
                if UUID(staff_id_str) != current_user.id:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to staff channel")
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid staff channel_id")
        else:
            # Treat as visitor UUID; must belong to the project
            try:
                vis_uuid = UUID(channel_id)
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid visitor channel_id")
            visitor = db.query(Visitor).filter(Visitor.id == vis_uuid, Visitor.deleted_at.is_(None)).first()
            if not visitor or visitor.project_id != project_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to visitor channel")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported channel_type")

    # 3) Validate file type/size
    # Allowed extensions
    allowed_exts = set((settings.ALLOWED_UPLOAD_EXTENSIONS or []))
    original_name = file.filename or "upload.bin"
    sanitized_name = _sanitize_filename(original_name)
    ext = sanitized_name.rsplit(".", 1)[-1].lower() if "." in sanitized_name else ""

    # MIME type
    mime = file.content_type or mimetypes.guess_type(sanitized_name)[0] or "application/octet-stream"

    if allowed_exts:
        if not ext or ext not in allowed_exts:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File type not allowed")
    else:
        # Fallback to MIME allowlist if extension list not set
        if settings.ALLOWED_FILE_TYPES and mime not in set(settings.ALLOWED_FILE_TYPES):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MIME type not allowed")

    max_bytes = int(settings.MAX_UPLOAD_SIZE_MB) * 1024 * 1024 if settings.MAX_UPLOAD_SIZE_MB else int(settings.MAX_FILE_SIZE)

    # 4) Build storage path
    ts_ms = int(time.time() * 1000)
    rand = secrets.token_hex(4)
    fname = f"{ts_ms}_{rand}_{sanitized_name}"

    date_dir = time.strftime("%Y-%m-%d")
    rel_path = f"chat/{project_id}/{channel_type}/{channel_id}/{date_dir}/{fname}"
    base_dir = Path(settings.UPLOAD_BASE_DIR).resolve()
    dest_path = base_dir / rel_path
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # 5) Save file in chunks
    total = 0
    try:
        with open(dest_path, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    try:
                        out.flush()
                        out.close()
                    finally:
                        try:
                            os.unlink(dest_path)
                        except Exception:
                            pass
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
                out.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        # Cleanup on failure
        try:
            if dest_path.exists():
                os.unlink(dest_path)
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"File storage failed: {e}")

    # 6) Persist metadata
    chat_file = ChatFile(
        project_id=project_id,
        channel_id=channel_id,
        channel_type=channel_type,
        file_name=original_name,
        file_path=rel_path,
        file_size=total,
        file_type=mime,
        uploaded_by_staff_id=(current_user.id if current_user else None),
        uploaded_by_platform_id=(platform.id if platform else None),
    )
    db.add(chat_file)
    db.commit()
    db.refresh(chat_file)

    # 7) Build response
    resp = ChatFileUploadResponse(
        file_id=str(chat_file.id),
        file_name=original_name,
        file_size=total,
        file_type=mime,
        file_url=f"/v1/chat/files/{chat_file.id}",
        channel_id=channel_id,
        channel_type=channel_type,
        uploaded_at=chat_file.created_at,
        uploaded_by=uploaded_by,
    )
    return resp



@router.get("/files/{file_id}", tags=["Chat"])
async def get_chat_file(
    file_id: UUID,
    platform_api_key: _Optional[str] = None,
    x_platform_api_key: _Optional[str] = Header(None, alias="X-Platform-API-Key"),
    credentials: _Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db),
):
    """Serve an uploaded chat file by ID.

    - Public access allowed by default
    - If auth is provided (JWT or platform API key), validate access to the channel
    """
    # 1) Lookup file metadata
    chat_file = (
        db.query(ChatFile)
        .filter(ChatFile.id == file_id, ChatFile.deleted_at.is_(None))
        .first()
    )
    if not chat_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    # 2) Optional auth/access validation
    current_user: _Optional[Staff] = None
    platform: _Optional[Platform] = None

    # JWT
    if credentials and credentials.credentials:
        payload = verify_token(credentials.credentials)
        if payload:
            username = payload.get("sub")
            if username:
                current_user = db.query(Staff).filter(Staff.username == username, Staff.deleted_at.is_(None)).first()
                if current_user and chat_file.project_id != current_user.project_id:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to file")

    # Platform API key (query or header)
    plat_key = platform_api_key or x_platform_api_key
    if plat_key and not current_user:
        platform = (
            db.query(Platform)
            .filter(Platform.api_key == plat_key, Platform.is_active == True, Platform.deleted_at.is_(None))
            .first()
        )
        if not platform:
            # If provided but invalid, treat as unauthorized
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid platform_api_key")
        # For customer service channels, enforce platform match via channel encoding
        if chat_file.channel_type == CHANNEL_TYPE_CUSTOMER_SERVICE:
            try:
                visitor_uuid = parse_visitor_channel_id(chat_file.channel_id)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file channel encoding")
            visitor = (
                db.query(Visitor)
                .filter(Visitor.id == visitor_uuid, Visitor.deleted_at.is_(None))
                .first()
            )
            if not visitor:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitor not found")
            if visitor.platform_id != platform.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform not authorized for file")
        else:
            # Personal channels are not accessible via platform API key
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform cannot access this file")

    # If no auth provided: public access allowed

    # 3) Build path and return FileResponse
    base_dir = Path(settings.UPLOAD_BASE_DIR).resolve()
    file_path = (base_dir / chat_file.file_path).resolve()
    # Ensure file path stays under base directory
    try:
        file_path.relative_to(base_dir)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid file path")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing from storage")

    # Build headers
    safe_name = chat_file.file_name or file_path.name
    safe_name = safe_name.replace("\r", " ").replace("\n", " ").strip()
    safe_name = safe_name or file_path.name

    normalized_name = unicodedata.normalize("NFKD", safe_name)
    ascii_name_bytes = normalized_name.encode("ascii", "ignore")
    ascii_name = ascii_name_bytes.decode("ascii") if ascii_name_bytes else ""
    ascii_name = "".join(
        ch if ch.isascii() and ch not in {'"', "\\", ";", ","} else "_"
        for ch in ascii_name
    ).strip()

    suffix = Path(safe_name).suffix
    if not ascii_name:
        ascii_name = f"file-{chat_file.id}{suffix}"
    elif suffix and not ascii_name.lower().endswith(suffix.lower()):
        ascii_name = f"{ascii_name}{suffix}"

    quoted_safe_name = quote(safe_name, safe="")

    headers = {
        "Content-Disposition": (
            f"inline; filename=\"{ascii_name}\"; filename*=UTF-8''{quoted_safe_name}"
        ),
        "Content-Length": str(chat_file.file_size or file_path.stat().st_size),
    }

    return FileResponse(
        path=str(file_path),
        media_type=chat_file.file_type or "application/octet-stream",
        headers=headers,
    )


@router.post(
    "/completions",
    summary="OpenAI-compatible chat completion",
    tags=["Chat"],
    description="""
    OpenAI ChatGPT API-compatible chat completion endpoint.

    This endpoint provides a fully compatible interface with OpenAI's ChatGPT API,
    allowing seamless integration with existing OpenAI client libraries and tools.

    **Authentication**: Use Platform API Key via `X-Platform-API-Key` header.

    **Request Format**: Compatible with OpenAI's chat completion request format.
    See: https://platform.openai.com/docs/api-reference/chat/create

    **Response Format**: Compatible with OpenAI's chat completion response format.
    See: https://platform.openai.com/docs/api-reference/chat/object

    **Streaming Support**: Set `stream=true` to receive Server-Sent Events (SSE).
    See: https://platform.openai.com/docs/api-reference/chat/streaming

    **Differences from `/completion` endpoint**:
    - Uses OpenAI-compatible request/response format
    - Supports standard OpenAI parameters (temperature, max_tokens, etc.)
    - Returns structured response with usage statistics
    - Supports both streaming and non-streaming modes

    **Internal Processing**:
    - Converts OpenAI format to internal message format
    - Publishes to Kafka for AI processing
    - Waits for AI response and converts back to OpenAI format
    """,
)
async def chat_completion_openai_compatible(
    req: OpenAIChatCompletionRequest,
    x_platform_api_key: str = Header(..., alias="X-Platform-API-Key"),
    db: Session = Depends(get_db),
):
    """OpenAI-compatible chat completion endpoint.

    Provides a fully compatible interface with OpenAI's ChatGPT API.
    Uses Platform API Key authentication via X-Platform-API-Key header.
    Supports both streaming (SSE) and non-streaming (JSON) responses.
    """
    # 1) Validate Platform API key and get project
    platform, project = _validate_platform_and_project(x_platform_api_key, db)

    # 2) Extract messages from OpenAI format
    user_message, system_message, platform_open_id = _extract_messages_from_openai_format(
        req.messages, req.user
    )

    # 3) Query visitor by platform_open_id to get visitor_id
    visitor = (
        db.query(Visitor)
        .filter(
            Visitor.platform_id == platform.id,
            Visitor.platform_open_id == platform_open_id,
            Visitor.deleted_at.is_(None),
        )
        .first()
    )

    # 4) Auto-register visitor if not found (with WuKongIM channel creation)
    if not visitor:
        visitor = await _create_visitor_with_channel(
            db=db,
            platform=platform,
            platform_open_id=platform_open_id,
        )

    # 5) Prepare correlation and session IDs using visitor_id
    client_msg_no = f"openai_{uuid4().hex}"
    channel_id_enc = build_visitor_channel_id(visitor.id)  # Use visitor.id, not platform_open_id
    channel_type = CHANNEL_TYPE_CUSTOMER_SERVICE
    session_id = f"{channel_id_enc}@{channel_type}"

    # 6) Get staff info if available
    staff_id, staff_cid = _get_staff_info(channel_id_enc, db)

    # 7) Build payload (use visitor_id as from_uid)
    payload = IncomingMessagePayload(
        from_uid=str(visitor.id),  # Use visitor_id, not platform_open_id
        channel_id=channel_id_enc,
        channel_type=channel_type,
        platform_id=str(platform.id),
        platform_type=platform.type,
        message_text=user_message,
        project_id=str(platform.project_id),
        project_api_key=project.api_key,
        client_msg_no=client_msg_no,
        session_id=session_id,
        received_at=int(time.time() * 1000),
        source="openai_compatible",
        extra=None,
        staff_id=staff_id,
        staff_cid=staff_cid,
        system_message=system_message,
        expected_output=None,
        ai_disabled=False,
    )

    # 7) Publish and subscribe to response stream
    queue, unsubscribe = await _publish_and_subscribe(payload, client_msg_no)

    # 8) Generate completion ID and timestamp (used for both streaming and non-streaming)
    completion_id = f"chatcmpl-{uuid4().hex[:24]}"
    created_timestamp = int(time.time())
    model_name = "tgo-ai"  # Fixed model name

    # 9) Handle streaming vs non-streaming response
    if req.stream:
        # Streaming response: return SSE with OpenAI-compatible chunks
        return StreamingResponse(
            _generate_openai_stream_chunks(
                queue=queue,
                unsubscribe=unsubscribe,
                completion_id=completion_id,
                created_timestamp=created_timestamp,
                model=model_name,
                timeout_seconds=120
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    # 10) Non-streaming response: collect all tokens and return JSON
    try:
        completion_text = await _collect_completion_from_stream(queue, timeout_seconds=120)
    finally:
        unsubscribe()

    # 11) Estimate token usage and build response
    prompt_tokens, completion_tokens, total_tokens = _estimate_token_usage(
        req.messages, completion_text
    )

    response = _build_openai_completion_response(
        completion_id=completion_id,
        created_timestamp=created_timestamp,
        model=model_name,
        completion_text=completion_text,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens
    )

    return response
