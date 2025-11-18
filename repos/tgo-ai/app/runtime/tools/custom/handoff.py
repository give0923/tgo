"""Team-level human handoff tool for requesting human support.

This tool is intentionally lightweight and safe-by-default:
- It returns a structured text confirmation instead of performing side effects
- It logs the request for observability
- It can be evolved later to trigger real handoff flows (DB/webhook/ticketing)
"""

from __future__ import annotations

from typing import Any, Optional
import uuid
import httpx

from agno.tools import Function

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_handoff_tool(*, team_id: str, session_id: str | None, user_id: str | None, project_id: str | None = None) -> Function:
    """Create a team-level tool that requests human support.

    Args:
        team_id: Current team ID
        session_id: Current session ID (optional)
        user_id: Current user ID (optional)
        project_id: Project ID for API Service events (optional but recommended)

    Returns:
        agno.tools.Function that can be added to Team.tools
    """

    def _uuid_or_none(value: Optional[str]) -> Optional[str]:
        try:
            return str(uuid.UUID(str(value))) if value else None
        except Exception:
            return None

    async def request_human_support(
        *,
        reason: str,
        urgency: str = "normal",
        channel: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Request human support: POST /v1/ai/events (manual_service.request).

        Follows docs/api_service.json AIServiceEvent schema. On failure, logs and
        returns a graceful confirmation without breaking the run.
        """
        # Assemble event payload per manual_service.request schema
        payload_metadata = {**(metadata or {}), "team_id": team_id, "user_id": user_id}
        if project_id:
            payload_metadata["project_id"] = project_id

        event_payload = {
            "event_type": "manual_service.request",
            "visitor_id": _uuid_or_none(user_id),
            "payload": {
                "reason": reason,
                "urgency": urgency,
                "channel": channel,
                "session_id": session_id,
                "metadata": payload_metadata,
            },
        }

        # Require base URL (keep UX graceful if missing)
        base_url = getattr(settings, "api_service_url", None)
        if not base_url:
            logger.warning(
                "api_service_url not configured; skipping API Service event call",
                extra={"team_id": team_id, "session_id": session_id},
            )
            return "抱歉，当前无法为您发起人工服务请求，我们已记录该问题并会尽快处理。请稍后再试或直接联系客服。"

        url = f"{base_url.rstrip('/')}/internal/ai/events"
        headers = {"Content-Type": "application/json"}

        try:
            timeout = httpx.Timeout(10.0, connect=5.0, read=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=event_payload, headers=headers)
                status = resp.status_code
                if status >= 400:
                    # Log response body for diagnostics; don't raise inside tool
                    try:
                        details = resp.json()
                    except Exception:
                        details = {"text": resp.text}
                    logger.error(
                        "Failed to ingest manual_service.request event",
                        extra={"status": status, "details": details},
                    )
                    return "抱歉，人工服务请求未能成功提交。请稍后重试或联系技术支持。"
        except httpx.HTTPError as exc:
            logger.error("HTTP error sending manual_service.request event", exc_info=exc)
            return "抱歉，网络异常导致人工服务请求未能提交。请稍后重试或联系技术支持。"
        except Exception as exc:
            logger.error("Unexpected error sending manual_service.request event", exc_info=exc)
            return "抱歉，出现异常，暂时无法为您发起人工服务。请稍后重试或联系技术支持。"

        # Success (202 or 200)
        logger.info(
            "manual_service.request event ingested",
            extra={"team_id": team_id, "session_id": session_id},
        )
        return (
            f"[handoff_requested] team={team_id} session={session_id or ''} "
            f"urgency={urgency} reason={reason} (event sent)"
        )

    return Function(
        name="request_human_support",
        description=(
            "当用户明确要求人工或你判断需要人工介入时调用此工具，用于发起人工支持流程。"
            "请在参数中简要说明原因与紧急程度。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "触发人工介入的原因（必填）",
                },
                "urgency": {
                    "type": "string",
                    "description": "紧急程度：low|normal|high|urgent（默认 normal）",
                },
                "channel": {
                    "type": "string",
                    "description": "期望的人工渠道（如 phone/wechat/email/ticket 等，可选）",
                },
                "metadata": {
                    "type": "object",
                    "description": "其他上下文字段（可选）",
                },
            },
            "required": ["reason"],
        },
        entrypoint=request_human_support,
        skip_entrypoint_processing=True,
    )

