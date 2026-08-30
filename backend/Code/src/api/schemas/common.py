"""Shared strict schema primitives and subject/language validation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...subject_languages import language_for_api_subject
from ...subject_registry import validate_component_for_subject, validate_top_level_subject_id


LanguageCode = Literal["de", "en", "fr"]


class ContractModel(BaseModel):
    """Base model that rejects unknown wire fields."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SubjectScope(ContractModel):
    """Validated top-level subject and optional SPF component selection."""

    subject_id: str
    component_subject_id: str | None = None

    @model_validator(mode="after")
    def validate_subject_scope(self):
        self.subject_id = validate_top_level_subject_id(self.subject_id)
        self.component_subject_id = validate_component_for_subject(
            self.subject_id, self.component_subject_id
        )
        return self


class LanguageSubjectScope(SubjectScope):
    """Subject scope with an explicit contract language code."""

    language: LanguageCode

    @model_validator(mode="after")
    def validate_subject_language(self):
        expected = language_for_api_subject(self.subject_id)
        if self.language != expected:
            raise ValueError(
                f"language must be {expected!r} for subject_id {self.subject_id!r}"
            )
        return self


class AcademicSubjectRequest(LanguageSubjectScope):
    """Common subject and school-context request fields."""

    academic_year: str = Field(min_length=1, max_length=20)
    grade_level: int = Field(ge=1, le=13)


class APIErrorDetail(ContractModel):
    """Stable error object nested inside every API error envelope."""

    code: str
    message: str
    detail: str | None = None
    retryable: bool = False
    request_id: str | None = None


class APIError(ContractModel):
    """Stable top-level error envelope."""

    error: APIErrorDetail


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for response defaults."""
    return datetime.now(timezone.utc)

