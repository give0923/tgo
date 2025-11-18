"""
In-memory pub/sub bus for platform SSE streaming, keyed by correlation_id.
- Provides subscribe(correlation_id) -> (queue, unsubscribe)
- Allows publishing events by correlation_id without blocking Kafka consumers
- Uses bounded per-subscriber queues to avoid unbounded memory growth
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Tuple, Callable, DefaultDict
from collections import defaultdict
import logging

logger = logging.getLogger("platform_stream_bus")

# Subscribers map: correlation_id -> list of queues
_subscribers: DefaultDict[str, List[asyncio.Queue]] = defaultdict(list)
_lock = asyncio.Lock()

DEFAULT_MAX_QUEUE = 100


async def subscribe(correlation_id: str, *, max_queue: int = DEFAULT_MAX_QUEUE) -> Tuple[asyncio.Queue, Callable[[], None]]:
    """Subscribe to events for a correlation_id.

    Returns a queue to receive events and an unsubscribe callback.
    """
    q: asyncio.Queue = asyncio.Queue(maxsize=max_queue)
    async with _lock:
        _subscribers[correlation_id].append(q)
        logger.debug("Subscribed queue to correlation_id=%s (subs=%d)", correlation_id, len(_subscribers[correlation_id]))

    def _unsubscribe() -> None:
        # Best-effort synchronous removal; safe to call multiple times
        lst = _subscribers.get(correlation_id)
        if lst is None:
            return
        try:
            lst.remove(q)
        except ValueError:
            pass
        if not lst:
            _subscribers.pop(correlation_id, None)
        # Try to drain queue to help GC
        try:
            while not q.empty():
                q.get_nowait()
        except Exception:
            pass

    return q, _unsubscribe


async def publish(correlation_id: str, event: Dict[str, Any]) -> int:
    """Publish event to all subscribers of correlation_id.

    Returns number of subscribers that accepted the event. Drops if a subscriber queue is full.
    """
    delivered = 0
    subs = _subscribers.get(correlation_id) or []
    if not subs:
        return 0

    # Use a snapshot to avoid issues if subscriptions change during iteration
    snapshot = list(subs)
    for q in snapshot:
        try:
            q.put_nowait(event)
            delivered += 1
        except asyncio.QueueFull:
            logger.warning("Stream bus queue full; dropping event for correlation_id=%s", correlation_id)
            continue
        except Exception as exc:
            logger.error("Failed to publish to subscriber: %s", exc)
            continue
    return delivered


async def publish_complete(correlation_id: str) -> None:
    """Optional helper to publish a complete event if needed."""
    await publish(correlation_id, {"event_type": "complete", "data": {}})

