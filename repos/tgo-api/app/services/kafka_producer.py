"""Kafka producer wrapper with optional aiokafka support.

Requires aiokafka (Kafka 4.x compatible). If not installed, publishing will be no-op with warnings.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

from app.core.config import settings
from app.schemas.messages import IncomingMessagePayload

logger = logging.getLogger("services.kafka_producer")

try:
    from aiokafka import AIOKafkaProducer  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    AIOKafkaProducer = None  # type: ignore


_producer: Optional["AIOKafkaProducer"] = None
_start_lock = asyncio.Lock()


async def start_producer() -> None:
    """Initialize and start the global Kafka producer if available."""
    global _producer
    if _producer is not None or AIOKafkaProducer is None:
        if AIOKafkaProducer is None:
            logger.warning("aiokafka not installed; Kafka producer disabled")
        return
    async with _start_lock:
        if _producer is None:
            _producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
            )
            await _producer.start()
            logger.info("Kafka producer started", extra={"bootstrap": settings.KAFKA_BOOTSTRAP_SERVERS})


async def stop_producer() -> None:
    """Stop the global Kafka producer if running."""
    global _producer
    if _producer is not None:
        try:
            await _producer.stop()
        finally:
            _producer = None
            logger.info("Kafka producer stopped")


async def publish(topic: str, payload: Any, *, key: Optional[bytes] = None) -> bool:
    """Publish a payload to the given Kafka topic.

    Returns True on success, False on failure or when producer is unavailable.
    """
    if _producer is None:
        # Try lazy start once
        await start_producer()
    if _producer is None:
        logger.warning("Kafka producer unavailable; drop message", extra={"topic": topic})
        return False
    try:
        await _producer.send_and_wait(topic, payload, key=key)
        return True
    except Exception as exc:
        logger.error("Kafka publish failed: %s", exc, extra={"topic": topic})
        return False


async def publish_incoming_message(payload: IncomingMessagePayload) -> bool:
    """Publish incoming message to the configured topic."""
    return await publish(settings.KAFKA_TOPIC_INCOMING_MESSAGES, payload.model_dump())

