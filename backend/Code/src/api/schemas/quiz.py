"""Quiz and quiz-question schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from .chat import SourceSnippet
from .common import AcademicSubjectRequest, ContractModel, LanguageCode


QuestionType = Literal["multiple_choice", "short_answer", "long_answer", "true_false"]


class QuizRequest(AcademicSubjectRequest):
    """User-scoped structured quiz-generation request."""

    learning_goal_id: str | None = None
    topic: str | None = Field(default=None, max_length=500)
    difficulty: Literal["easy", "medium", "hard", "adaptive"] = "adaptive"
    question_count: int = Field(default=5, ge=1, le=20)
    material_ids: list[str] = Field(default_factory=list)


class QuizQuestion(ContractModel):
    """One typed quiz question from the frontend contract."""

    question_id: str
    question_type: QuestionType
    prompt: str
    options: list[str] = Field(default_factory=list)
    points: float = Field(default=1, gt=0)
    learning_goal_id: str | None = None
    correct_index: int | None = Field(default=None, ge=0)
    expected_answer: str | None = None
    correct_answer: str | None = None
    explanation: str | None = None


class Quiz(ContractModel):
    """Generated quiz payload."""

    quiz_id: str
    subject_id: str
    component_subject_id: str | None = None
    language: LanguageCode
    title: str
    difficulty: Literal["easy", "medium", "hard", "adaptive"]
    questions: list[QuizQuestion]
    sources: list[SourceSnippet] = Field(default_factory=list)
    used_model: str
    created_at: datetime
