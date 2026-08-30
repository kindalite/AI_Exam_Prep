"""Provider-neutral model response and capability types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    """The result of asking any configured generation provider for text."""

    text: str
    ok: bool
    error: str | None = None


@dataclass(frozen=True)
class ProviderStatus:
    """Safe provider status with no credentials or response bodies."""

    provider: str
    model: str
    endpoint: str
    mode: str
    reachable: bool
    message: str
    supports_streaming: bool
    supports_vision: bool
