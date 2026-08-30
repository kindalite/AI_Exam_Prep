"""Local feedback storage in JSON Lines format."""

from __future__ import annotations

import json
from pathlib import Path

from .config import AppConfig, load_config
from .utils import ensure_directory, utc_timestamp


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
    """Read feedback records from a JSONL file."""
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records

