"""Small performance measurement helpers for slow local operations."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterator

from .app_logging import append_log, ensure_log_directories


@dataclass(frozen=True)
class PerformanceMetric:
    """One measured operation duration."""

    operation: str
    duration_seconds: float
    ok: bool
    detail: str = ""


def performance_log_path(config) -> Path:
    """Return the JSONL performance diagnostics log."""
    return ensure_log_directories(config)["performance"] / "operation_timings.jsonl"


def record_metric(config, metric: PerformanceMetric) -> dict:
    """Persist a redacted performance metric."""
    return append_log(performance_log_path(config), "performance_metric", asdict(metric))


@contextmanager
def measure_operation(config, operation: str, detail: str = "") -> Iterator[None]:
    """Measure an operation and log success/failure duration."""
    start = time.perf_counter()
    ok = False
    try:
        yield
        ok = True
    finally:
        record_metric(config, PerformanceMetric(operation, round(time.perf_counter() - start, 4), ok, detail))
