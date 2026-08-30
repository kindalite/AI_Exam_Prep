"""Persistent timed attempt session state for quiz and exam modes."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .user_data_paths import get_user_root, sanitize_username
from .utils import ensure_directory, utc_timestamp


@dataclass(frozen=True)
class TimedAttemptSession:
    """A timed quiz or exam session that survives Streamlit reruns."""

    attempt_id: str
    user_id: str
    subject_key: str
    mode: str
    started_at: str
    ends_at: str
    duration_seconds: int
    status: str
    question_set_path: str
    solution_set_path: str
    submitted_answers_path: str | None
    grading_report_path: str | None


def _now() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(timezone.utc)


def _parse_time(value: str) -> datetime:
    """Parse a stored ISO timestamp."""
    return datetime.fromisoformat(value)


def session_path(user_id: str, attempt_id: str, config) -> Path:
    """Return the local JSON session path."""
    return get_user_root(user_id, config) / "attempts" / f"{attempt_id}_session.json"


def create_timed_session(user_id: str, subject_key: str, mode: str, duration_minutes: int, question_set_path: str, solution_set_path: str, config) -> TimedAttemptSession:
    """Create and persist a running timed attempt session."""
    safe_user = sanitize_username(user_id)
    started = _now()
    duration_seconds = int(duration_minutes * 60)
    session = TimedAttemptSession(uuid.uuid4().hex, safe_user, subject_key, mode, started.isoformat(timespec="seconds"), (started + timedelta(seconds=duration_seconds)).isoformat(timespec="seconds"), duration_seconds, "running", question_set_path, solution_set_path, None, None)
    save_timed_session(session, config)
    return session


def save_timed_session(session: TimedAttemptSession, config) -> dict:
    """Persist a timed attempt session."""
    path = session_path(session.user_id, session.attempt_id, config)
    ensure_directory(path.parent)
    row = asdict(session)
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    return row


def load_timed_session(user_id: str, attempt_id: str, config) -> TimedAttemptSession | None:
    """Load a timed session if it exists."""
    path = session_path(user_id, attempt_id, config)
    if not path.exists():
        return None
    return TimedAttemptSession(**json.loads(path.read_text(encoding="utf-8")))


def seconds_remaining(session: TimedAttemptSession) -> int:
    """Return remaining whole seconds for a session."""
    return max(0, int((_parse_time(session.ends_at) - _now()).total_seconds()))


def mark_session_status(session: TimedAttemptSession, status: str, config, submitted_answers_path: str | None = None, grading_report_path: str | None = None) -> TimedAttemptSession:
    """Persist a changed session status."""
    updated = TimedAttemptSession(session.attempt_id, session.user_id, session.subject_key, session.mode, session.started_at, session.ends_at, session.duration_seconds, status, session.question_set_path, session.solution_set_path, submitted_answers_path if submitted_answers_path is not None else session.submitted_answers_path, grading_report_path if grading_report_path is not None else session.grading_report_path)
    save_timed_session(updated, config)
    return updated


def refresh_expired_session(session: TimedAttemptSession, config) -> TimedAttemptSession:
    """Mark a running session expired when the timer has elapsed."""
    if session.status == "running" and seconds_remaining(session) <= 0:
        status = "submitted" if getattr(config, "allow_auto_submit_on_timer_end", True) else "expired"
        return mark_session_status(session, status, config)
    return session


def solution_is_visible(session: TimedAttemptSession, config) -> bool:
    """Return True only when solutions may be shown."""
    if not getattr(config, "hide_solutions_until_graded", True):
        return True
    return session.status == "graded"
