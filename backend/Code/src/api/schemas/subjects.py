"""Subject catalogue and learning-goal schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from .common import ContractModel, LanguageCode
from .materials import MaterialSourceModel


class SubjectComponentModel(ContractModel):
    """Nested concrete component of the virtual SPF subject."""

    subject_id: str
    display_name: str
    language: LanguageCode


class SubjectModel(ContractModel):
    """One top-level subject exposed to the frontend."""

    subject_id: str
    display_name: str
    language: LanguageCode
    is_virtual: bool = False
    components: list[SubjectComponentModel] = Field(default_factory=list)
    corpus_keys: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    indexed_materials: int = Field(default=0, ge=0)
    learning_goal_count: int = Field(default=0, ge=0)
    last_indexed_at: datetime | None = None


class LearningGoalModel(ContractModel):
    """Structured learning goal owned by the Python backend."""

    learning_goal_id: str
    subject_id: str
    component_subject_id: str | None = None
    title: str
    text: str
    order: int = Field(default=0, ge=0)
    source: MaterialSourceModel | None = None
