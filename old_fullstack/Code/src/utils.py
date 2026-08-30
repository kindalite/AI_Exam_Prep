"""Small shared helpers used across the Alim Study Assistant codebase."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def utc_timestamp() -> str:
    """Return the current UTC time as an ISO string for logs and metadata."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not exist and return the same path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_text_if_exists(path: Path) -> str:
    """Read a UTF-8 text file, returning an empty string if it is missing."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_text_if_missing(path: Path, content: str) -> None:
    """Create a text file only when it does not already exist."""
    if not path.exists():
        ensure_directory(path.parent)
        path.write_text(content, encoding="utf-8")


def safe_preview(text: str, limit: int = 280) -> str:
    """Return a short one-line preview of a longer text block."""
    clean_text = " ".join(text.split())
    if len(clean_text) <= limit:
        return clean_text
    return clean_text[: limit - 3] + "..."


def join_non_empty(parts: Iterable[str], separator: str = "\n\n") -> str:
    """Join text parts while skipping empty values."""
    return separator.join(part.strip() for part in parts if part and part.strip())

