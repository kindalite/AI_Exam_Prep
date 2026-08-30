"""AI study-plan proposal schemas (not frontend planner CRUD state)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import Field

from .chat import SourceSnippet
from .common import AcademicSubjectRequest, ContractModel, LanguageCode


class AvailableTimeSlot(ContractModel):
    """One frontend-provided local study window in 24-hour HH:MM format."""

    date: date
    start_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")


class StudyPlanRequest(AcademicSubjectRequest):
    """Request for a proposal; it never writes frontend planner state."""

    exam_date: date
    hours_per_week: float = Field(gt=0, le=168)
    weak_topics: list[str] = Field(default_factory=list, max_length=30)
    learning_goal_ids: list[str] = Field(default_factory=list, max_length=50)
    available_time_slots: list[AvailableTimeSlot] = Field(default_factory=list, max_length=100)
    max_daily_minutes: int = Field(default=120, ge=15, le=720)
    material_ids: list[str] = Field(default_factory=list)


class StudyPlanItem(ContractModel):
    """One proposed study action."""

    item_id: str
    date: date
    start_time: str | None = Field(default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end_time: str | None = Field(default=None, pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    title: str
    description: str
    duration_minutes: int = Field(gt=0, le=1440)
    activity_type: Literal["review", "practice", "quiz", "mock_exam", "break"]
    learning_goal_id: str | None = None


class StudyPlan(ContractModel):
    """AI-generated plan proposal returned to the frontend."""

    study_plan_id: str
    subject_id: str
    component_subject_id: str | None = None
    language: LanguageCode
    exam_date: date
    items: list[StudyPlanItem]
    summary: str
    sources: list[SourceSnippet] = Field(default_factory=list)
    used_model: str
    created_at: datetime
