"""Framework-neutral Stage-1 student identity bridge."""

from __future__ import annotations

from dataclasses import dataclass

from ..user_data_paths import sanitize_username


@dataclass(frozen=True)
class StudentContext:
    """Sanitized student identity and optional request correlation metadata."""

    student_id: str
    request_id: str | None = None

    def __post_init__(self) -> None:
        """Sanitize identity at construction so raw IDs cannot reach storage."""
        raw = self.student_id.strip()
        if not raw:
            raise ValueError("student_id is required")
        object.__setattr__(self, "student_id", sanitize_username(raw))


def resolve_student_context(
    raw_student_id: str | None,
    *,
    fallback_student_id: str | None = None,
    request_id: str | None = None,
) -> StudentContext:
    """Resolve an API header value, optionally using an explicit dev fallback."""
    chosen = raw_student_id.strip() if raw_student_id and raw_student_id.strip() else ""
    if not chosen and fallback_student_id:
        chosen = fallback_student_id.strip()
    if not chosen:
        raise ValueError("X-Student-Id is required for this operation")
    return StudentContext(chosen, request_id=request_id)

