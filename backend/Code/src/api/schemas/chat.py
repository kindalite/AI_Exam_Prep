"""Chat request, response, source, and retrieval-summary schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from .common import AcademicSubjectRequest, ContractModel, LanguageCode


class SourceSnippet(ContractModel):
    """A source excerpt grounded in real retrieval metadata."""

    source_id: str
    material_id: str | None = None
    material_name: str
    section: str | None = None
    page: int | None = Field(default=None, ge=1)
    snippet: str
    score: float | None = None
    url: str | None = None


class RetrievalSummary(ContractModel):
    """Transparent summary of retrieval work for a generated answer."""

    chunks_considered: int = Field(ge=0)
    chunks_used: int = Field(ge=0)
    collection_names: list[str] = Field(default_factory=list)
    material_ids: list[str] = Field(default_factory=list)
    learning_goal_id: str | None = None


class ChatRequest(AcademicSubjectRequest):
    """Non-streaming or streaming subject-chat request."""

    thread_id: str = Field(min_length=1, max_length=200)
    question: str = Field(min_length=1, max_length=4000)
    learning_goal_id: str | None = None
    material_ids: list[str] = Field(default_factory=list)
    top_k: int = Field(default=6, ge=1, le=24)
    include_sources: bool = True
    stream: bool = False

    @field_validator("question")
    @classmethod
    def question_must_not_be_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("question must not be empty")
        return value


class ChatResponse(ContractModel):
    """Grounded assistant answer returned without owning transcript storage."""

    thread_id: str
    message_id: str
    answer: str
    sources: list[SourceSnippet] = Field(default_factory=list)
    exam_tip: str | None = None
    used_model: str
    retrieval_summary: RetrievalSummary
    language: LanguageCode
    created_at: datetime

