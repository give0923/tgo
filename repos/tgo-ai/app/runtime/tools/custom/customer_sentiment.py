"""Team-level tool to track/update customer sentiment/state information.

Patterns mirrored from handoff and customer_info tools:
- POST /v1/ai/events with AIServiceEvent envelope
- Friendly Chinese error messages; technical details logged
- Non-intrusive on failure (no break in team run)
"""

from __future__ import annotations

from typing import Any, Optional
import uuid
import httpx

from agno.tools import Function

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_customer_sentiment_tool(
    *,
    team_id: str,
    session_id: str | None,
    user_id: str | None,
    project_id: str | None = None,
) -> Function:
    """Create a team-level tool that updates customer sentiment/state.

    Args:
        team_id: Current team ID
        session_id: Current session ID (optional)
        user_id: Current user ID (optional)
        project_id: Project ID (optional; used in payload.metadata for tracking)

    Returns:
        agno.tools.Function that can be added to Team.tools
    """

    def _uuid_or_none(value: Optional[str]) -> Optional[str]:
        try:
            return str(uuid.UUID(str(value))) if value else None
        except Exception:
            return None

    async def update_customer_sentiment(
        *,
        satisfaction: Optional[str] = None,
        emotion: Optional[str] = None,
        intent: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Update customer sentiment/state: POST /v1/ai/events (customer_sentiment.update)."""
        # Validate and normalize numeric scales for satisfaction/emotion (0-5)
        def _parse_scale(val: Any) -> int:
            s = str(val).strip()
            try:
                iv = int(s)
            except Exception:
                try:
                    f = float(s)
                except Exception:
                    raise ValueError
                if not float(f).is_integer():
                    raise ValueError
                iv = int(f)
            if iv < 0 or iv > 5:
                raise ValueError
            return iv

        sat_val = None
        emo_val = None
        if satisfaction not in (None, ""):
            try:
                sat_val = _parse_scale(satisfaction)
            except Exception:
                return "满意度和情绪的数值必须在0-5之间，0表示未知。"
        if emotion not in (None, ""):
            try:
                emo_val = _parse_scale(emotion)
            except Exception:
                return "满意度和情绪的数值必须在0-5之间，0表示未知。"

        # Build provided dict (intent remains string-based)
        provided: dict[str, Any] = {}
        if sat_val is not None:
            provided["satisfaction"] = sat_val
        if emo_val is not None:
            provided["emotion"] = emo_val
        if intent not in (None, ""):
            provided["intent"] = intent

        if not provided:
            return "请至少提供一个需要更新的客户状态字段，例如满意度、情绪或意图。"

        # Prepare payload metadata and envelope per AIServiceEvent schema
        payload_metadata = {**(metadata or {}), "team_id": team_id, "user_id": user_id}
        if project_id:
            payload_metadata["project_id"] = project_id

        event_payload = {
            "event_type": "customer_sentiment.update",
            "visitor_id": _uuid_or_none(user_id),
            "payload": {
                "session_id": session_id,
                "sentiment": provided,
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
            return "抱歉，当前无法为您更新客户状态，我们已记录该问题并会尽快处理。请稍后再试或直接联系客服。"

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
                        "Failed to ingest customer_sentiment.update event",
                        extra={"status": status, "details": details},
                    )
                    return "抱歉，客户状态更新未能成功提交。请稍后重试或联系技术支持。"
        except httpx.HTTPError as exc:
            logger.error("HTTP error sending customer_sentiment.update event", exc_info=exc)
            return "抱歉，网络异常导致客户状态更新未能提交。请稍后重试或联系技术支持。"
        except Exception as exc:
            logger.error("Unexpected error sending customer_sentiment.update event", exc_info=exc)
            return "抱歉，出现异常，暂时无法为您更新客户状态。请稍后重试或联系技术支持。"

        # Success
        updated_keys = ", ".join(provided.keys())
        logger.info(
            "customer_sentiment.update event ingested",
            extra={"team_id": team_id, "session_id": session_id, "updated": updated_keys},
        )
        return f"已记录客户状态更新：{updated_keys}。"

    return Function(
        name="update_customer_sentiment",
        description=(
            "当你在对话中识别到客户满意度、情绪或意图发生变化时，调用此工具以记录/更新客户状态。"
            "可跟踪的信息包括：满意度（0-5数值，0表示未知，数值越高表示越满意）、情绪（0-5数值，0表示未知，数值越高表示情绪越积极）、"
            "意图（如 purchase/inquiry/complaint/support）；字段均为可选，支持部分更新。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "satisfaction": {"type": "integer", "minimum": 0, "maximum": 5, "description": "满意度，0-5数值（0=未知，1=非常不满意，5=非常满意）"},
                "emotion": {"type": "integer", "minimum": 0, "maximum": 5, "description": "情绪，0-5数值（0=未知，1=非常消极，5=非常积极）"},
                "intent": {"type": "string", "description": "意图（可选）"},
                "metadata": {"type": "object", "description": "其他上下文字段（可选）"},
            },
            "required": [],
        },
        entrypoint=update_customer_sentiment,
        skip_entrypoint_processing=True,
    )

