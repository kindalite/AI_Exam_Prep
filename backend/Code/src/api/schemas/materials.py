"""Indexed material and material-source schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .common import ContractModel


class MaterialSourceModel(ContractModel):
    """Citation-oriented metadata for material content."""

    source_id: str
    source_name: str
    source_layer: str
    page: int | None = Field(default=None, ge=1)
    modality: str | None = None
    url: str | None = None


class MaterialModel(ContractModel):
    """One uploaded or canonical material item and its index state."""

    material_id: str
    subject_id: str
    component_subject_id: str | None = None
    material_name: str
    file_name: str
    media_type: str
    section: str | None = None
    archived: bool = False
    status: Literal["uploaded", "indexing", "indexed", "failed", "needs_review"]
    size_bytes: int | None = Field(default=None, ge=0)
    chunks_indexed: int = Field(default=0, ge=0)
    created_at: datetime
    indexed_at: datetime | None = None
    warning: str | None = None
    sources: list[MaterialSourceModel] = Field(default_factory=list)


class DocumentImportResponse(ContractModel):
    """API-shaped result of one parsed and indexed upload."""

    material_id: str
    name: str
    type: str
    section: str
    language: str
    pages: int | None = Field(default=None, ge=1)
    chunks_indexed: int = Field(ge=0)
    status: Literal["indexed", "needs_review"]
    warnings: list[str] = Field(default_factory=list)
    added_at: datetime
