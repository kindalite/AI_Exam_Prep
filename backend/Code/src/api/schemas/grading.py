"""AI grading request and exact Swiss-grade result schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator, model_validator

from .chat import SourceSnippet
from .common import AcademicSubjectRequest, ContractModel


class GradingRequest(AcademicSubjectRequest):
    """Answer and rubric context submitted for AI practice grading."""

    question: str = Field(min_length=1, max_length=12000)
    student_answer: str = Field(min_length=1, max_length=30000)
    max_points: float = Field(gt=0)
    marking_scheme: str | None = Field(default=None, max_length=20000)
    material_ids: list[str] = Field(default_factory=list)

    @field_validator("question", "student_answer")
    @classmethod
    def text_must_not_be_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value


class GradingResult(ContractModel):
    """Structured evaluation with the unrounded Swiss formula value."""

    points_awarded: float = Field(ge=0)
    max_points: float = Field(gt=0)
    swiss_grade: float = Field(ge=1, le=6)
    grade_formula: str
    strengths: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    improvement_advice: list[str] = Field(default_factory=list)
    rubric_used: list[str] = Field(default_factory=list)
    sources: list[SourceSnippet] = Field(default_factory=list)
    graded_at: datetime
    used_model: str

    @model_validator(mode="after")
    def points_must_not_exceed_max(self):
        if self.points_awarded > self.max_points:
            raise ValueError("points_awarded must not exceed max_points")
        return self
