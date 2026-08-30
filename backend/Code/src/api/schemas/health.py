"""Model and backend health response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .common import ContractModel


class VectorStoreStatus(ContractModel):
    """Safe vector-store status included in backend health."""

    store_type: str
    reachable: bool
    collection_count: int = Field(ge=0)
    collection_names: list[str] = Field(default_factory=list)
    message: str = ""


class ModelStatus(ContractModel):
    """Safe provider-neutral model status."""

    provider: str
    model: str
    endpoint: str
    mode: Literal["local", "remote"]
    reachable: bool
    latency_ms: float = Field(ge=0)
    embedding_model: str
    fallback_provider: str | None = None
    message: str = ""
    supports_streaming: bool = False
    supports_vision: bool = False


class BackendHealth(ContractModel):
    """Process and dependency health response."""

    status: Literal["ok", "degraded", "error"]
    api_version: str
    uptime_seconds: float = Field(ge=0)
    vector_store: VectorStoreStatus
    model_server_reachable: bool
    model_provider: str
    indexed_top_level_subjects: int = Field(ge=0, le=15)
    checked_at: datetime
