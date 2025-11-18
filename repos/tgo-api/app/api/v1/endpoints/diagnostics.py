"""Diagnostic endpoints for debugging Kafka consumers and system health."""

import asyncio
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter()


@router.get("/kafka-consumers")
async def kafka_consumer_status() -> Dict[str, Any]:
    """Get status of all Kafka consumer tasks for debugging."""
    from app.services.kafka_consumers import ai_processor, wukong_forwarder, platform_forwarder

    def task_status(task: asyncio.Task | None) -> Dict[str, Any]:
        if task is None:
            return {"status": "not_created", "done": None, "cancelled": None}
        return {
            "status": "running" if not task.done() else "done",
            "done": task.done(),
            "cancelled": task.cancelled(),
            "exception": str(task.exception()) if task.done() and not task.cancelled() else None,
        }

    return {
        "ai_processor": {
            "task": task_status(ai_processor._consumer_task),
            "stop_event_set": ai_processor._stop_event.is_set(),
        },
        "wukong_forwarder": {
            "task": task_status(wukong_forwarder._consumer_task),
            "stop_event_set": wukong_forwarder._stop_event.is_set(),
        },
        "platform_forwarder": {
            "task": task_status(platform_forwarder._consumer_task),
            "stop_event_set": platform_forwarder._stop_event.is_set(),
        },
    }

