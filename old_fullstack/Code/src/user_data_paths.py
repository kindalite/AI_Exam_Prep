"""Per-user local filesystem paths and collection names."""

from __future__ import annotations

import re
from pathlib import Path

from .utils import ensure_directory


SUBJECT_CHILDREN = ("notes", "syllabus", "criteria")


def sanitize_username(username: str) -> str:
    """Return a safe user id for local path and collection names."""
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", username.strip().lower()).strip("_")
    return safe or "user"


def get_user_root(user_id: str, config) -> Path:
    """Return the root folder for one isolated user."""
    root = getattr(config, "user_data_root", None) or config.data_dir / "users"
    return Path(root) / sanitize_username(user_id)


def get_user_subject_root(user_id: str, subject_key: str, config) -> Path:
    """Return one user's subject folder."""
    return get_user_root(user_id, config) / "subjects" / subject_key


def ensure_user_subject_structure(user_id: str, subject_key: str, config) -> Path:
    """Create the standard per-user subject folder structure."""
    subject_root = get_user_subject_root(user_id, subject_key, config)
    for child in SUBJECT_CHILDREN:
        ensure_directory(subject_root / child)
    for name, title in [("learning_goals.md", "Learning Goals"), ("exam_criteria.md", "Exam Criteria")]:
        path = subject_root / name
        if not path.exists():
            path.write_text(f"# {title}: {subject_key}\n\nAdd {title.lower()} here.\n", encoding="utf-8")
    return subject_root


def ensure_user_data_structure(user_id: str, config, subject_keys: list[str] | None = None) -> Path:
    """Create the local folders used by one user."""
    root = get_user_root(user_id, config)
    for relative in [
        "chat_history",
        "chat_media/images",
        "chat_media/audio",
        "chat_media/transcripts",
        "chat_media/image_descriptions",
        "generated_practice/quizzes",
        "generated_practice/exams",
        "generated_practice/solution_sets",
        "attempts",
        "reports",
        "rag_exports",
    ]:
        ensure_directory(root / relative)
    for subject_key in subject_keys or []:
        ensure_user_subject_structure(user_id, subject_key, config)
    return root


def user_subject_collection_name(user_id: str, subject_key: str) -> str:
    """Return a vector collection name scoped to one user and subject."""
    return f"user_{sanitize_username(user_id)}__subject_{subject_key}"


def user_memory_collection_name(user_id: str, subject_key: str) -> str:
    """Return a vector collection name for one user's RAG memory."""
    return f"user_{sanitize_username(user_id)}__memory_{subject_key}"


def relative_to_user(path: Path, user_id: str, config) -> str:
    """Return a user-root relative path when possible."""
    root = get_user_root(user_id, config)
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
