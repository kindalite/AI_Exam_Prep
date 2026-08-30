"""Local JSONL storage for practice attempts and topic mastery."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .utils import ensure_directory, utc_timestamp


@dataclass(frozen=True)
class PracticeAttempt:
    """One local practice or chat performance record."""

    attempt_id: str
    timestamp: str
    subject_key: str
    topic: str
    learning_goal: str
    feature: str
    difficulty: str
    question: str
    student_answer: str
    model_feedback: str
    points_achieved: float | None
    maximum_points: float | None
    grade: float | None
    self_rating: int | None
    time_spent_seconds: int | None
    source_chunk_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


def new_attempt(**kwargs) -> PracticeAttempt:
    """Create a practice attempt with id and timestamp defaults."""
    data = {
        "attempt_id": uuid.uuid4().hex,
        "timestamp": utc_timestamp(),
        "subject_key": "",
        "topic": "",
        "learning_goal": "",
        "feature": "chat",
        "difficulty": "medium",
        "question": "",
        "student_answer": "",
        "model_feedback": "",
        "points_achieved": None,
        "maximum_points": None,
        "grade": None,
        "self_rating": None,
        "time_spent_seconds": None,
        "source_chunk_ids": [],
        "tags": [],
    }
    data.update(kwargs)
    return PracticeAttempt(**data)


def _log_file(config) -> Path:
    """Return the configured attempts JSONL file."""
    configured = getattr(config, "performance_log_file", None)
    if configured is not None:
        return Path(configured)
    data_dir = Path(getattr(config, "data_dir", Path("data")))
    return data_dir / "performance" / "attempts.jsonl"


def save_practice_attempt(attempt: PracticeAttempt, config) -> dict:
    """Append one practice attempt to the local JSONL log."""
    path = _log_file(config)
    ensure_directory(path.parent)
    row = asdict(attempt)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def read_practice_attempts(config, subject_key: str | None = None) -> list[dict]:
    """Read practice attempts, optionally filtered by subject."""
    path = _log_file(config)
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if subject_key is None or row.get("subject_key") == subject_key:
            rows.append(row)
    return rows


def summarize_performance(subject_key: str, config) -> dict:
    """Summarize attempts and grades for one subject."""
    rows = read_practice_attempts(config, subject_key)
    grades = [float(row["grade"]) for row in rows if row.get("grade") is not None]
    return {
        "subject_key": subject_key,
        "attempt_count": len(rows),
        "average_grade": round(sum(grades) / len(grades), 2) if grades else None,
        "topic_mastery": topic_mastery_scores(subject_key, config),
        "recent_attempts": rows[-10:],
    }


def topic_mastery_scores(subject_key: str, config) -> dict[str, float]:
    """Return simple topic mastery scores from recent point ratios or self ratings."""
    buckets: dict[str, list[float]] = {}
    for row in read_practice_attempts(config, subject_key):
        topic = row.get("topic") or row.get("learning_goal") or "general"
        score: float | None = None
        if row.get("points_achieved") is not None and row.get("maximum_points"):
            score = float(row["points_achieved"]) / float(row["maximum_points"])
        elif row.get("self_rating") is not None:
            score = float(row["self_rating"]) / 5.0
        if score is not None:
            buckets.setdefault(topic, []).append(max(0.0, min(1.0, score)))
    return {topic: round(sum(values[-5:]) / len(values[-5:]), 2) for topic, values in buckets.items()}
