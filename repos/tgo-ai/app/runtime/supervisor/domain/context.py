"""Helper types for the supervisor runtime layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from app.runtime.supervisor.orchestration.orchestrator import CoordinationOrchestrator
from app.runtime.supervisor.models.coordination import CoordinationRequest
from app.runtime.supervisor.streaming.workflow_events import WorkflowEventEmitter


@dataclass(slots=True)
class CoordinationRuntimeContext:
    """Container for prepared coordination runtime dependencies."""

    orchestrator: CoordinationOrchestrator
    request: CoordinationRequest
    team_id: str
    execution_strategy: str
    auth_headers: Dict[str, str]
    workflow_events: Optional[WorkflowEventEmitter] = None


__all__ = ["CoordinationRuntimeContext"]
