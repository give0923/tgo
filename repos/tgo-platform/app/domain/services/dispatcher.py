from __future__ import annotations
import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import Platform
from app.domain.entities import NormalizedMessage, ChatCompletionRequest
from app.domain.ports import TgoApiClient, SSEManager, PlatformAdapter
from app.domain.services.adapters import SimpleStdoutAdapter, EmailAdapter, WeComAdapter


def _expected_output_for(ptype: str) -> str | None:
    p = (ptype or "").lower()
    if p == "wecom":
        return "text"
    if p == "email":
        return "markdown"
    return None


def _default_system_message_for(ptype: str) -> str | None:
    p = (ptype or "").lower()
    if p == "email":
        return (
            "You are responding to an email. Please format your response as a professional "
            "email reply with appropriate greeting, body, and closing."
        )
    if p == "wecom":
        return None
    return None



async def select_adapter_for_target(msg: NormalizedMessage, platform: Platform) -> PlatformAdapter:
    """Choose platform adapter based on platform.type and per-platform config.

    For type="email", construct EmailAdapter using SMTP settings from Platform.config.
    For type="wecom", construct WeComAdapter using per-platform config and message sender as target.
    Otherwise, default to SimpleStdoutAdapter.
    """
    ptype = (platform.type or "").lower()
    if ptype == "email":
        cfg = platform.config or {}
        smtp_host = cfg.get("smtp_host")
        smtp_port = int(cfg.get("smtp_port", 587))
        smtp_username = cfg.get("smtp_username")
        smtp_password = cfg.get("smtp_password")
        smtp_use_tls = bool(cfg.get("smtp_use_tls", False))
        from_addr = smtp_username
        # Determine addressing and subject from message extras
        to_addr = (msg.extra or {}).get("email_to") or msg.from_uid
        subject = (msg.extra or {}).get("subject") or ""
        if not (smtp_host and smtp_username and smtp_password and from_addr and to_addr):
            # Fallback to stdout if config incomplete
            return SimpleStdoutAdapter()
        return EmailAdapter(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            smtp_use_tls=smtp_use_tls,
            to_addr=to_addr,
            from_addr=from_addr,
            subject=subject,
        )
    if ptype == "wecom":
        cfg = platform.config or {}
        corp_id = cfg.get("corp_id")
        agent_id = cfg.get("agent_id")
        app_secret = cfg.get("app_secret")
        to_user = msg.from_uid
        wc = ((msg.extra or {}).get("wecom") or {})
        is_from_colleague = bool(wc.get("is_from_colleague", True))
        open_kfid = wc.get("open_kfid")
        external_userid = wc.get("external_userid") or msg.from_uid
        if not (corp_id and agent_id and app_secret and to_user):
            return SimpleStdoutAdapter()
        return WeComAdapter(
            corp_id=corp_id,
            agent_id=str(agent_id),
            app_secret=app_secret,
            to_user=to_user,
            is_from_colleague=is_from_colleague,
            open_kfid=open_kfid,
            external_userid=external_userid,
        )
    return SimpleStdoutAdapter()


async def process_message(
    msg: NormalizedMessage,
    db: AsyncSession,
    tgo_api_client: TgoApiClient,
    sse_manager: SSEManager,
    visitor_id: str | None = None,
) -> str | None:
    """End-to-end orchestration using DB platform config + tgo-api SSE + adapter output.

    Returns the final reply text if available (for non-streaming adapters), otherwise None.
    """
    if not getattr(msg, "platform_api_key", None):
        raise RuntimeError("platform_api_key missing on NormalizedMessage")
    for attempt in range(3):
        try:
            # Fetch platform by id only if needed for adapter selection/config
            platform = await db.scalar(select(Platform).where(Platform.id == msg.platform_id))

            # Choose platform-specific expected output format for tgo-api
            ptype = ((platform.type if platform else msg.platform_type) or "").lower()
            expected_output = _expected_output_for(ptype)

            uid_source = visitor_id or msg.from_uid or ""
            # Default system message by platform; allow explicit override via msg.extra["system_message"]
            default_system_message = _default_system_message_for(ptype)
            try:
                system_message = ((msg.extra or {}).get("system_message")) or default_system_message
            except Exception:
                system_message = default_system_message
            req = ChatCompletionRequest(
                api_key=msg.platform_api_key,
                message=msg.content,
                from_uid=uid_source,
                system_message=system_message,
                expected_output=expected_output,
                extra=msg.extra,
                timeout_seconds=settings.request_timeout_seconds,
            )
            frames = tgo_api_client.chat_completion(req)
            events = sse_manager.stream_events(frames)

            adapter = await select_adapter_for_target(msg, platform=platform) if platform else SimpleStdoutAdapter()

            if adapter.supports_stream:
                async for ev in events:
                    payload = ev.payload or {}
                    if payload.get("event_type") == "ai_disabled":
                        logging.info("[DISPATCH] AI disabled; skipping reply (platform_id=%s)", msg.platform_id)
                        return None
                    await adapter.send_incremental(ev)
                return None
            else:
                # Aggregate manually to detect ai_disabled early
                chunks: list[str] = []
                async for ev in events:
                    payload = ev.payload or {}
                    et = payload.get("event_type")
                    if et == "ai_disabled":
                        logging.info("[DISPATCH] AI disabled; skipping reply (platform_id=%s)", msg.platform_id)
                        return None
                    if ev.event in {"error", "disconnected"}:
                        break
                    if et in {"team_run_content"}:
                        data = payload.get("data", {})
                        text = data.get("content")
                        if text:
                            chunks.append(text)
                    if et in {"workflow_completed", "team_run_completed", "workflow_failed"}:
                        break
                final = {"text": "".join(chunks)}
                await adapter.send_final(final)
                return (final.get("text") if isinstance(final, dict) else None)
        except Exception as e:
            if attempt == 2:
                raise
            logging.warning(
                "[DISPATCH] attempt %s failed for platform_id=%s: %s", attempt + 1, msg.platform_id, e, exc_info=True
            )
            await asyncio.sleep(2 ** attempt)

