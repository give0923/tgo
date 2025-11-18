"""Kafka consumer that forwards AI responses to the TGO Platform Service.

Stub implementation: consumes tgo.ai.responses and logs TODO. Keeps streaming
payload structure consistent with other consumers.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from app.core.config import settings

logger = logging.getLogger("consumers.platform_forwarder")

try:
    from aiokafka import AIOKafkaConsumer  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    AIOKafkaConsumer = None  # type: ignore

_consumer_task: Optional[asyncio.Task] = None
_stop_event = asyncio.Event()


async def _run_consumer() -> None:
    if AIOKafkaConsumer is None:
        logger.warning("aiokafka not installed; Platform forwarder consumer disabled")
        return

    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_AI_RESPONSES,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_CONSUMER_GROUP_PLATFORM_FORWARDER,
        enable_auto_commit=True,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    await consumer.start()
    logger.info("Platform forwarder consumer started", extra={"topic": settings.KAFKA_TOPIC_AI_RESPONSES})

    # Lazy import to avoid circulars at module import time
    from app.services.platform_stream_bus import publish as stream_publish

    try:
        async for msg in consumer:
            if _stop_event.is_set():
                break
            evt: Dict[str, Any] = msg.value or {}
            client_msg_no: Optional[str] = evt.get("client_msg_no")
            if not client_msg_no:
                logger.debug("Platform forwarder: event missing client_msg_no; skipping")
                continue

            # Publish into in-memory bus for SSE listeners
            delivered = await stream_publish(client_msg_no, evt)
            logger.debug(
                "Platform forwarder delivered event to SSE bus",
                extra={"client_msg_no": client_msg_no, "delivered": delivered, "event_type": evt.get("event_type")},
            )
    finally:
        await consumer.stop()
        logger.info("Platform forwarder consumer stopped")


async def start_platform_forwarder() -> None:
    global _consumer_task
    if _consumer_task and not _consumer_task.done():
        return
    _stop_event.clear()
    _consumer_task = asyncio.create_task(_run_consumer())


async def stop_platform_forwarder() -> None:
    _stop_event.set()
    if _consumer_task:
        try:
            await asyncio.wait_for(_consumer_task, timeout=5)
        except Exception:
            _consumer_task.cancel()

