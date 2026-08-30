"""Local feedback storage in JSON Lines format."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import AppConfig, load_config
from .utils import ensure_directory, utc_timestamp
from .user_data_paths import get_user_root, sanitize_username


def save_feedback(
    subject: str,
    feature: str,
    user_task: str,
    app_answer: str,
    rating: int,
    comment: str,
    source_chunk_ids: list[str] | None = None,
    config: AppConfig | None = None,
) -> dict:
    """Append one feedback record to the local JSONL feedback file."""
    app_config = config or load_config()
    ensure_directory(app_config.feedback_file.parent)
    record = {
        "timestamp": utc_timestamp(),
        "subject": subject,
        "feature": feature,
        "user_task": user_task,
        "app_answer": app_answer,
        "rating": rating,
        "comment": comment,
        "source_chunk_ids": source_chunk_ids or [],
    }
    with app_config.feedback_file.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=True) + "\n")
    return record


def read_feedback(path: Path) -> list[dict]:
    """Read valid feedback records while tolerating malformed JSONL lines."""
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                value = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(value, dict):
                records.append(value)
    return records


def api_feedback_path(student_id: str, config: AppConfig) -> Path:
    """Return the isolated append-only API feedback log for one student."""
    return get_user_root(sanitize_username(student_id), config) / "feedback" / "feedback.jsonl"


def save_api_feedback(
    *,
    student_id: str,
    category: str,
    rating: int | None,
    message: str | None,
    route: str | None,
    thread_id: str | None,
    message_id: str | None,
    subject_id: str | None,
    language: str | None,
    app_version: str | None,
    config: AppConfig,
) -> dict:
    """Append privacy-minimal frontend feedback to a student-specific log."""
    created_at = datetime.now(timezone.utc)
    record = {
        "feedback_id": "fb_" + uuid.uuid4().hex,
        "student_id": sanitize_username(student_id),
        "category": category,
        "rating": rating,
        "message": message,
        "route": route,
        "thread_id": thread_id,
        "message_id": message_id,
        "subject_id": subject_id,
        "language": language,
        "app_version": app_version,
        "created_at": created_at.isoformat().replace("+00:00", "Z"),
    }
    path = api_feedback_path(student_id, config)
    ensure_directory(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record
