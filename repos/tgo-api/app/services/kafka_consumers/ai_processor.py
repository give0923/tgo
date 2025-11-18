"""Kafka AI processing consumer.

Consumes incoming messages from Kafka, calls AI service (streaming), and publishes
AI response events to the responses topic. Optional aiokafka dependency.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, Optional

from app.core.config import settings
from app.services.ai_client import AIServiceClient
from app.services.kafka_producer import publish as kafka_publish, start_producer
from app.schemas.messages import IncomingMessagePayload

from app.services.run_registry import run_registry

logger = logging.getLogger("consumers.ai_processor")

try:
    from aiokafka import AIOKafkaConsumer  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    AIOKafkaConsumer = None  # type: ignore

_consumer_task: Optional[asyncio.Task] = None
_stop_event = asyncio.Event()

# Concurrency controls
MAX_CONCURRENCY = int(getattr(settings, "KAFKA_AI_PROCESSOR_MAX_CONCURRENCY", 5))
_semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
_inflight_tasks: set[asyncio.Task] = set()


async def _process_one(message_count: int, payload: IncomingMessagePayload, client: AIServiceClient) -> None:
    """Process a single incoming message end-to-end without blocking the consumer loop."""
    async with _semaphore:
        try:
            logger.info(f"AI processor: Parsing message #{message_count}...")
            # Extract typed fields from payload
            message_text: str = payload.message_text or ""
            client_msg_no: Optional[str] = payload.client_msg_no
            session_id: str = payload.session_id or f"sess_{uuid.uuid4().hex}"
            user_id: str = payload.from_uid or ""
            channel_id: str = payload.channel_id or ""
            channel_type: int = int(payload.channel_type or 0)
            project_id: Optional[str] = getattr(payload, "project_id", None)
            staff_cid: str = payload.staff_cid or ""  # staff chat id

            logger.info(
                f"AI processor: Parsed message #{message_count} fields",
                extra={
                    "has_project_id": bool(project_id),
                    "has_text": bool(message_text),
                    "has_user": bool(user_id),
                    "has_channel": bool(channel_id),
                    "client_msg_no": client_msg_no,
                    "session_id": session_id,
                },
            )

            if not project_id or not message_text or not user_id or not channel_id:
                logger.warning(
                    f"AI processor: Skipping message #{message_count} due to missing fields",
                    extra={
                        "has_project_id": bool(project_id),
                        "has_text": bool(message_text),
                        "has_user": bool(user_id),
                        "has_channel": bool(channel_id),
                        "client_msg_no": client_msg_no,
                    },
                )
                return

            logger.info(
                f"AI processor: Processing incoming message #{message_count}",
                extra={"client_msg_no": client_msg_no, "session_id": session_id},
            )

            # Respect ai_disabled flag: skip AI service call entirely
            if payload.ai_disabled:
                logger.info(
                    "AI processor: AI processing disabled for message, skipping AI service call",
                    extra={"client_msg_no": client_msg_no, "session_id": session_id},
                )
                return

            try:
                logger.info(f"AI processor: Starting AI stream for message #{message_count}")
                chunk_count = 0
                workflow_completed = False
                async for _, event_payload in client.run_supervisor_agent_stream(
                    message=message_text,
                    project_id=str(project_id or ""),
                    team_id="default",
                    session_id=session_id,
                    user_id=user_id,
                    enable_memory=True,
                    system_message=payload.system_message,
                    expected_output=payload.expected_output,
                ):
                    chunk_count += 1
                    # Forward streaming payloads as-is (enrich with session/correlation)
                    if isinstance(event_payload, dict):
                        event_type = event_payload.get("event_type", "team_run_content")

                        # Maintain mapping client_msg_no -> run_id for cancellation-by-client
                        if client_msg_no:
                            try:
                                if event_type == "team_run_started":
                                    meta = event_payload.get("metadata") or {}
                                    data_obj = event_payload.get("data") or {}
                                    run_id = meta.get("run_id") or data_obj.get("run_id")
                                    print("kafka - run_id--->",run_id,client_msg_no)
                                    if run_id:
                                        should_cancel, reason = await run_registry.set_mapping_and_check_pending(
                                            client_msg_no=client_msg_no,
                                            run_id=str(run_id),
                                            project_id=str(project_id or ""),
                                            api_key=None,
                                            session_id=session_id,
                                        )
                                        if should_cancel:
                                            try:
                                                await client.cancel_supervisor_run(
                                                    project_id=str(project_id or ""),
                                                    run_id=str(run_id),
                                                    reason=reason,
                                                )
                                                logger.info(
                                                    "AI processor: Pending cancel executed at run start",
                                                    extra={"client_msg_no": client_msg_no, "run_id": run_id},
                                                )
                                            except Exception as cancel_exc:
                                                logger.warning(
                                                    "AI processor: Failed to cancel pending run at start: %s",
                                                    cancel_exc,
                                                    extra={"client_msg_no": client_msg_no, "run_id": run_id},
                                                )
                                elif event_type in {"workflow_completed", "team_run_completed", "workflow_failed", "team_run_failed", "error"}:
                                    await run_registry.clear(client_msg_no)
                            except Exception as reg_exc:
                                logger.debug(
                                    "AI processor: run_registry handling error (ignored): %s",
                                    reg_exc,
                                    extra={"client_msg_no": client_msg_no},
                                )

                        event_payload.setdefault("event_type", event_type)

                        # Publish the event
                        await kafka_publish(
                            settings.KAFKA_TOPIC_AI_RESPONSES,
                            {
                                "session_id": session_id,
                                "client_msg_no": client_msg_no,
                                "from_uid": staff_cid,
                                "channel_id": channel_id,
                                "channel_type": channel_type,
                                **event_payload,
                            },
                        )

                logger.info(
                    f"AI processor: AI stream completed for message #{message_count}",
                    extra={
                        "chunk_count": chunk_count,
                        "session_id": session_id,
                        "workflow_completed": workflow_completed,
                    },
                )
            except Exception as exc:  # pragma: no cover
                logger.error(
                    f"AI processor: AI streaming failed for message #{message_count}: %s",
                    exc,
                    extra={"session_id": session_id},
                    exc_info=True,
                )
            finally:
                logger.info(
                    f"AI processor: Finished processing message #{message_count}, ready for next message"
                )
        except Exception as exc:
            # Critical: ensure one message failure doesn't kill the task
            logger.error(
                f"AI processor: Unhandled error for message #{message_count}: %s",
                exc,
                exc_info=True,
            )
            await asyncio.sleep(0.5)
            logger.info(f"AI processor: Task recovered from error, ending task")


async def _run_consumer() -> None:
    if AIOKafkaConsumer is None:
        logger.warning("aiokafka not installed; AI processor consumer disabled")
        return

    logger.info("AI processor: Initializing consumer...")
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_INCOMING_MESSAGES,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_CONSUMER_GROUP_AI_PROCESSOR,
        enable_auto_commit=True,
        auto_offset_reset="earliest",  # ensure consumption of existing msgs when no committed offsets
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    client = AIServiceClient()

    logger.info("AI processor: Starting consumer connection...")
    await consumer.start()
    logger.info("AI processor: Consumer connected, starting producer...")
    await start_producer()  # ensure producer available for responses
    logger.info(
        "AI processor consumer started - entering message loop",
        extra={"topic": settings.KAFKA_TOPIC_INCOMING_MESSAGES},
    )

    message_count = 0
    try:
        logger.info("AI processor: Waiting for messages in async for loop...")
        async for msg in consumer:
            message_count += 1
            logger.info(
                f"AI processor: Received message #{message_count} from Kafka",
                extra={
                    "offset": msg.offset,
                    "partition": msg.partition,
                    "timestamp": msg.timestamp,
                    "key": msg.key,
                },
            )
            if _stop_event.is_set():
                logger.info("AI processor: Stop event detected, breaking loop")
                break

            try:
                payload_dict = msg.value or {}
                payload = IncomingMessagePayload.model_validate(payload_dict)
                # Dispatch processing as a background task to avoid blocking consumption
                task = asyncio.create_task(_process_one(message_count, payload, client))
                _inflight_tasks.add(task)
                task.add_done_callback(lambda t: _inflight_tasks.discard(t))
                logger.info(
                    f"AI processor: Dispatched message #{message_count} to background task",
                )
            except Exception as exc:
                logger.error(
                    f"AI processor: Unhandled error dispatching task for message #{message_count}: %s",
                    exc,
                    exc_info=True,
                )
    except asyncio.CancelledError:
        logger.warning("AI processor: Consumer task was cancelled")
        raise
    except Exception as exc:
        logger.error("AI processor: Fatal error in consumer loop: %s", exc, exc_info=True)
        raise
    finally:
        logger.info(f"AI processor: Stopping consumer (processed {message_count} messages total)")
        await consumer.stop()
        logger.info("AI processor consumer stopped")
        # Wait for in-flight tasks to finish (best-effort)
        pending = set(_inflight_tasks)
        if pending:
            logger.info(f"AI processor: Waiting for {len(pending)} in-flight task(s) to finish")
            res = await asyncio.wait(pending, timeout=20)
            not_done = res[1]
            if not_done:
                logger.warning(f"AI processor: {len(not_done)} task(s) still running after timeout; cancelling")
                for t in not_done:
                    t.cancel()


async def start_ai_processor() -> None:
    global _consumer_task
    if _consumer_task and not _consumer_task.done():
        logger.info("AI processor: Consumer task already running, skipping start")
        return
    logger.info("AI processor: Starting new consumer task")
    _stop_event.clear()
    _consumer_task = asyncio.create_task(_run_consumer())
    logger.info(f"AI processor: Consumer task created: {_consumer_task}")


async def stop_ai_processor() -> None:
    logger.info("AI processor: Stop requested")
    _stop_event.set()
    if _consumer_task:
        logger.info(f"AI processor: Waiting for consumer task to finish: {_consumer_task}")
        try:
            await asyncio.wait_for(_consumer_task, timeout=5)
            logger.info("AI processor: Consumer task finished gracefully")
        except asyncio.TimeoutError:
            logger.warning("AI processor: Consumer task timeout, cancelling")
            _consumer_task.cancel()
        except Exception as exc:
            logger.error("AI processor: Error stopping consumer task: %s", exc)
            _consumer_task.cancel()

