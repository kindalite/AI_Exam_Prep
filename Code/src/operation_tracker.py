"""Track long operations so Streamlit reruns can recover cleanly."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field

from .app_logging import append_log, ensure_log_directories


@dataclass
class OperationState:
    """Serializable state for one operation."""

    operation_id: str
    name: str
    status: str
    current_step: str
    started_at: float
    updated_at: float
    warnings: list[str] = field(default_factory=list)
    error: str = ""

    @property
    def elapsed_seconds(self) -> float:
        """Return elapsed wall-clock seconds."""
        return max(0.0, time.time() - self.started_at)


class OperationTracker:
    """In-memory operation tracker with redacted diagnostic logging."""

    def __init__(self, config, slow_threshold_seconds: float = 20.0) -> None:
        self.config = config
        self.slow_threshold_seconds = slow_threshold_seconds
        self.operations: dict[str, OperationState] = {}

    def start(self, name: str, step: str) -> OperationState:
        now = time.time()
        state = OperationState(uuid.uuid4().hex, name, "running", step, now, now)
        self.operations[state.operation_id] = state
        self._log("operation_started", state)
        return state

    def update(self, operation_id: str, step: str) -> OperationState:
        state = self.operations[operation_id]
        state.current_step = step
        state.updated_at = time.time()
        if state.elapsed_seconds > self.slow_threshold_seconds and not state.warnings:
            state.warnings.append(f"Operation exceeded {self.slow_threshold_seconds:.0f}s: {state.name}")
        self._log("operation_updated", state)
        return state

    def succeed(self, operation_id: str, step: str = "completed") -> OperationState:
        state = self.operations[operation_id]
        state.status = "success"
        state.current_step = step
        state.updated_at = time.time()
        self._log("operation_succeeded", state)
        return state

    def fail(self, operation_id: str, error: str) -> OperationState:
        state = self.operations[operation_id]
        state.status = "error"
        state.error = error
        state.updated_at = time.time()
        self._log("operation_failed", state)
        return state

    def _log(self, event: str, state: OperationState) -> None:
        path = ensure_log_directories(self.config)["app_runs"] / "operations.jsonl"
        append_log(path, event, asdict(state))
