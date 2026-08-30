"""Session-scoped web-search permission helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WebPermission:
    """Current permission for optional public web retrieval."""

    allowed: bool
    remember_for_session: bool = False


def permission_from_choice(choice: str, remember: bool = False) -> WebPermission:
    """Map a UI choice to a web permission value."""
    normalized = choice.strip().lower()
    return WebPermission(normalized in {"search internet", "search", "yes", "allow"}, remember)
