"""Team-level tool to collect and update customer information.

This tool mirrors the patterns used by the human handoff tool:
- Event POST to /v1/ai/events using the AIServiceEvent envelope
- Friendly Chinese messages for failures; technical details logged
- Safe-by-default behavior (does not break team run on failure)
"""

from __future__ import annotations

from typing import Any, Optional
import uuid
import httpx

from agno.tools import Function

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_customer_info_tool(
    *,
    team_id: str,
    session_id: str | None,
    user_id: str | None,
    project_id: str | None = None,
) -> Function:
    """Create a team-level tool that updates customer info.

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

    async def update_customer_info(
        *,
        email: Optional[str] = None,
        wechat: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None,
        sex: Optional[str] = None,
        age: Optional[str] = None,
        company: Optional[str] = None,
        position: Optional[str] = None,
        address: Optional[str] = None,
        birthday: Optional[str] = None,
        extra_info: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Update customer information: POST /v1/ai/events (customer_info.update)."""
        # Validate at least one field provided (excluding metadata)
        provided = {
            k: v
            for k, v in {
                "email": email,
                "wechat": wechat,
                "phone": phone,
                "name": name,
                "sex": sex,
                "age": age,
                "company": company,
                "position": position,
                "address": address,
                "birthday": birthday,
            }.items()
            if v not in (None, "")
        }
        if not provided:
            return "请至少提供一个需要更新的客户信息字段，例如邮箱、电话、微信、姓名等。"

        # Prepare payload metadata and envelope per AIServiceEvent schema
        payload_metadata = {**(metadata or {}), "team_id": team_id, "user_id": user_id}
        if project_id:
            payload_metadata["project_id"] = project_id

        customer_data = dict(provided)
        if extra_info:
            customer_data["extra_info"] = extra_info

        event_payload = {
            "event_type": "customer_info.update",
            "visitor_id": _uuid_or_none(user_id),
            "payload": {
                "session_id": session_id,
                "customer": customer_data,
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
            return "抱歉，当前无法为您更新客户资料，我们已记录该问题并会尽快处理。请稍后再试或直接联系客服。"

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
                        "Failed to ingest customer_info.update event",
                        extra={"status": status, "details": details},
                    )
                    return "抱歉，客户资料更新未能成功提交。请稍后重试或联系技术支持。"
        except httpx.HTTPError as exc:
            logger.error("HTTP error sending customer_info.update event", exc_info=exc)
            return "抱歉，网络异常导致客户资料更新未能提交。请稍后重试或联系技术支持。"
        except Exception as exc:
            logger.error("Unexpected error sending customer_info.update event", exc_info=exc)
            return "抱歉，出现异常，暂时无法为您更新客户资料。请稍后重试或联系技术支持。"

        # Success
        updated_keys = ", ".join(provided.keys())
        logger.info(
            "customer_info.update event ingested",
            extra={"team_id": team_id, "session_id": session_id, "updated": updated_keys},
        )
        return f"已提交客户信息更新：{updated_keys}。感谢配合！"

    return Function(
        name="update_customer_info",
        description=(
            "当客户提供联系方式或个人信息时，调用此工具以记录或更新客户资料。"
            "可收集的信息包括：邮箱、微信、电话、姓名、性别、公司、职位、地址、生日、备注等；"
            "所有字段均为可选，支持部分更新。"
        ),
        parameters={
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "邮箱（可选）"},
                "wechat": {"type": "string", "description": "微信号（可选）"},
                "phone": {"type": "string", "description": "手机号（可选）"},
                "name": {"type": "string", "description": "姓名（可选）"},
                "sex": {"type": "string", "description": "性别（可选）"},
                "age": {"type": "string", "description": "年龄（可选）"},
                "company": {"type": "string", "description": "公司（可选）"},
                "position": {"type": "string", "description": "职位（可选）"},
                "address": {"type": "string", "description": "地址（可选）"},
                "birthday": {"type": "string", "description": "生日（可选）"},
                "extra_info": {"type": "object", "description": "扩展信息：存储其他未预定义的客户信息，如 Telegram、偏好等（可选）"},
                "metadata": {"type": "object", "description": "其他上下文字段（可选）"},
            },
            "required": [],
        },
        entrypoint=update_customer_info,
        skip_entrypoint_processing=True,
    )

