"""Feedback submission and acknowledgement schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from ...subject_registry import validate_top_level_subject_id
from ...subject_languages import language_for_api_subject
from .common import ContractModel, LanguageCode


class FeedbackEntry(ContractModel):
    """Privacy-minimal feedback tied to an optional AI result correlation ID."""

    category: Literal["answer_quality", "bug", "feature_request", "content_gap", "other"]
    rating: int | None = Field(default=None, ge=1, le=5)
    message: str | None = Field(default=None, max_length=4000)
    route: str | None = Field(default=None, max_length=500)
    thread_id: str | None = None
    message_id: str | None = None
    subject_id: str | None = None
    language: LanguageCode | None = None
    app_version: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validate_feedback(self):
        if self.rating is None and not (self.message and self.message.strip()):
            raise ValueError("one of message or rating must be present")
        if self.subject_id is not None:
            self.subject_id = validate_top_level_subject_id(self.subject_id)
            if self.language is not None and self.language != language_for_api_subject(self.subject_id):
                raise ValueError("language does not match subject_id")
        return self


class FeedbackResponse(ContractModel):
    """Feedback persistence acknowledgement."""

    feedback_id: str
    created_at: datetime
