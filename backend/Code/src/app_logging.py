"""Safe local diagnostic logging for app runs and user sessions."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from .utils import ensure_directory, safe_preview, utc_timestamp


SENSITIVE_KEYS = {"password", "passcode", "secret", "token", "credential", "api_key", "authorization"}
REDACTION_PATTERN = re.compile(r"(?i)(password|secret|token|api[_-]?key|authorization)\s*[:=]\s*\S+")


def bug_review_root(config) -> Path:
    """Return the local bug-review diagnostics root."""
    return Path(getattr(config, "project_root", Path("."))) / "bug_review"


def ensure_log_directories(config) -> dict[str, Path]:
    """Create the diagnostic folders required by the stability prompt."""
    root = bug_review_root(config)
    folders = {
        "app_runs": root / "app_runs",
        "user_sessions": root / "user_sessions",
        "crashes": root / "crashes",
        "performance": root / "performance",
        "test_reports": root / "test_reports",
    }
    for folder in folders.values():
        ensure_directory(folder)
    return folders


def redact_value(value: Any, preview_limit: int = 240) -> Any:
    """Redact secrets and cap long private text previews before logging."""
    if isinstance(value, dict):
        return {key: "[REDACTED]" if key.lower() in SENSITIVE_KEYS else redact_value(item, preview_limit) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_value(item, preview_limit) for item in value]
    if isinstance(value, str):
        return safe_preview(REDACTION_PATTERN.sub(r"\1=[REDACTED]", value), preview_limit)
    return value


def append_log(path: Path, event: str, payload: dict[str, Any] | None = None, preview_limit: int = 240) -> dict[str, Any]:
    """Append one redacted JSONL diagnostic event."""
    ensure_directory(path.parent)
    row = {"timestamp": utc_timestamp(), "event": event, "payload": redact_value(payload or {}, preview_limit)}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row


def new_app_run_log(config) -> Path:
    """Create a unique app-run log path without writing private data."""
    folders = ensure_log_directories(config)
    return folders["app_runs"] / f"app_run_{utc_timestamp().replace(':', '-')}_{uuid.uuid4().hex[:8]}.jsonl"


def new_user_session_log(config, user_id: str) -> Path:
    """Create a unique anonymized user-session log path."""
    folders = ensure_log_directories(config)
    anonymized = uuid.uuid5(uuid.NAMESPACE_URL, str(user_id)).hex[:12]
    return folders["user_sessions"] / f"user_{anonymized}_{utc_timestamp().replace(':', '-')}.jsonl"
