"""Mock-exam and exam-question schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .chat import SourceSnippet
from .common import AcademicSubjectRequest, ContractModel, LanguageCode
from .quiz import QuestionType


class MockExamRequest(AcademicSubjectRequest):
    """User-scoped structured mock-exam generation request."""

    total_points: float = Field(gt=0, le=500)
    difficulty: Literal["easy", "medium", "hard", "adaptive"] = "adaptive"
    topics: list[str] = Field(default_factory=list, max_length=20)
    learning_goal_ids: list[str] = Field(default_factory=list, max_length=50)
    material_ids: list[str] = Field(default_factory=list)


class MockExamQuestion(ContractModel):
    """One typed mock-exam question with explicit point allocation."""

    question_id: str
    question_type: QuestionType
    prompt: str
    points: float = Field(gt=0)
    options: list[str] = Field(default_factory=list)
    learning_goal_id: str | None = None
    marking_criteria: list[str] = Field(default_factory=list)
    model_answer: str | None = None


class MockExam(ContractModel):
    """Generated mock-exam payload."""

    mock_exam_id: str
    subject_id: str
    component_subject_id: str | None = None
    language: LanguageCode
    title: str
    difficulty: Literal["easy", "medium", "hard", "adaptive"]
    total_points: float = Field(gt=0)
    questions: list[MockExamQuestion]
    sources: list[SourceSnippet] = Field(default_factory=list)
    used_model: str
    created_at: datetime
