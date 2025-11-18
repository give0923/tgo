"""In-memory registry for mapping client_msg_no to AI run metadata.

This is used to support cancelling running AI supervisor runs by client_msg_no.
- ai_processor records the mapping when the stream emits team_run_started (run_id available)
- HTTP endpoint can request cancellation by client_msg_no; if run_id not known yet, we mark pending
- When run_id arrives and pending is set, ai_processor will immediately invoke cancel

Note: This registry is per-process. For multi-instance deployments, use a shared store (e.g., Redis).
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple


DEFAULT_TTL_SECONDS = 15 * 60  # 15 minutes


@dataclass
class RunEntry:
    client_msg_no: str
    project_id: Optional[str]
    api_key: Optional[str]
    session_id: Optional[str]
    run_id: Optional[str] = None
    pending_cancel: bool = False
    cancel_reason: Optional[str] = None
    ts: float = 0.0  # last update timestamp

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


class RunRegistry:
    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._by_client: Dict[str, RunEntry] = {}
        self._lock = asyncio.Lock()

    async def _prune_locked(self) -> None:
        now = time.time()
        expired = [k for k, v in self._by_client.items() if now - (v.ts or 0.0) > self._ttl]
        for k in expired:
            self._by_client.pop(k, None)

    async def get(self, client_msg_no: str) -> Optional[RunEntry]:
        async with self._lock:
            await self._prune_locked()
            return self._by_client.get(client_msg_no)

    async def clear(self, client_msg_no: str) -> None:
        async with self._lock:
            self._by_client.pop(client_msg_no, None)

    async def mark_cancel_pending(self, client_msg_no: str, *, reason: Optional[str], project_id: Optional[str], api_key: Optional[str]) -> None:
        """Mark a cancel request as pending if run_id not yet known.
        If an entry exists, update flags; otherwise create a shell entry so that ai_processor can act when run_id arrives.
        """
        async with self._lock:
            await self._prune_locked()
            entry = self._by_client.get(client_msg_no)
            now = time.time()
            if entry is None:
                entry = RunEntry(
                    client_msg_no=client_msg_no,
                    project_id=project_id,
                    api_key=api_key,
                    session_id=None,
                    run_id=None,
                    pending_cancel=True,
                    cancel_reason=reason,
                    ts=now,
                )
                self._by_client[client_msg_no] = entry
            else:
                entry.pending_cancel = True
                entry.cancel_reason = reason
                if project_id:
                    entry.project_id = entry.project_id or project_id
                if api_key:
                    entry.api_key = entry.api_key or api_key
                entry.ts = now

    async def set_mapping_and_check_pending(
        self,
        *,
        client_msg_no: str,
        run_id: str,
        project_id: Optional[str],
        api_key: Optional[str],
        session_id: Optional[str],
    ) -> Tuple[bool, Optional[str]]:
        """Set the mapping with run_id. Returns (should_cancel_now, reason).
        If there was a pending cancel, this prompts caller to cancel immediately.
        """
        async with self._lock:
            await self._prune_locked()
            now = time.time()
            entry = self._by_client.get(client_msg_no)
            if entry is None:
                entry = RunEntry(
                    client_msg_no=client_msg_no,
                    project_id=project_id,
                    api_key=api_key,
                    session_id=session_id,
                    run_id=run_id,
                    pending_cancel=False,
                    cancel_reason=None,
                    ts=now,
                )
                self._by_client[client_msg_no] = entry
                return (False, None)

            # Update existing entry
            entry.run_id = run_id
            entry.session_id = session_id or entry.session_id
            entry.project_id = entry.project_id or project_id
            entry.api_key = entry.api_key or api_key
            entry.ts = now
            if entry.pending_cancel:
                # Reset pending flag but keep record until caller triggers cancel
                reason = entry.cancel_reason
                entry.pending_cancel = False
                return (True, reason)
            return (False, None)


# Global instance
run_registry = RunRegistry()

