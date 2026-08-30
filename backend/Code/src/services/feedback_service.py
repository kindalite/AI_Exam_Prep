"""Framework-neutral feedback persistence service."""

from __future__ import annotations

from ..config import AppConfig
from ..feedback import save_api_feedback, save_feedback
from .identity_service import StudentContext


def submit_feedback(
    *,
    subject_key: str,
    feature: str,
    user_task: str,
    app_answer: str,
    rating: int,
    comment: str,
    source_chunk_ids: list[str] | None = None,
    config: AppConfig | None = None,
) -> dict:
    """Validate and persist one feedback record."""
    if rating < 1 or rating > 5:
        raise ValueError("rating must be between 1 and 5")
    return save_feedback(
        subject_key,
        feature,
        user_task,
        app_answer,
        rating,
        comment,
        source_chunk_ids,
        config=config,
    )


def submit_api_feedback(
    *,
    category: str,
    rating: int | None,
    message: str | None,
    route: str | None,
    thread_id: str | None,
    message_id: str | None,
    subject_id: str | None,
    language: str | None,
    app_version: str | None,
    student: StudentContext,
    config: AppConfig,
) -> dict:
    """Persist one validated feedback entry in the current student's store."""
    if rating is None and not (message and message.strip()):
        raise ValueError("one of message or rating must be present")
    return save_api_feedback(
        student_id=student.student_id,
        category=category,
        rating=rating,
        message=message,
        route=route,
        thread_id=thread_id,
        message_id=message_id,
        subject_id=subject_id,
        language=language,
        app_version=app_version,
        config=config,
    )
