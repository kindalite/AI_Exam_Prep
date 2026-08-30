"""Framework-neutral subject, goals, material-context, and stats services."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..config import AppConfig
from ..retrieval import RetrievalResult, load_exam_criteria, load_learning_goals, retrieve_for_subject
from ..services.material_service import material_inventory
from ..stats import recent_attempts_table, subject_performance_summary
from ..subject_registry import Subject, build_subject_registry, corpus_keys_for_request, get_subject, subjects_for_display
from ..user_data_paths import get_user_subject_root


@dataclass(frozen=True)
class LearningGoalRecord:
    """Framework-neutral parsed learning goal with source metadata."""

    learning_goal_id: str
    subject_id: str
    component_subject_id: str | None
    title: str
    text: str
    order: int
    source_name: str
    source_layer: str


@dataclass(frozen=True)
class SubjectReadMetadata:
    """Truthful read metadata derived from backend files/manifests."""

    corpus_keys: tuple[str, ...]
    indexed_materials: int
    learning_goal_count: int
    last_indexed_at: datetime | None
    topics: tuple[str, ...]


def list_subjects(config: AppConfig) -> list[Subject]:
    """Return current executable subjects in display order."""
    return subjects_for_display(config)


def resolve_subject(subject_key: str, config: AppConfig) -> Subject:
    """Resolve a current executable subject key."""
    return get_subject(subject_key, config)


def subject_registry(config: AppConfig) -> dict[str, Subject]:
    """Return the current executable registry."""
    return build_subject_registry(config)


def read_learning_goals(subject: Subject) -> str:
    """Read the stored learning-goal Markdown for a subject."""
    return load_learning_goals(subject)


def read_exam_criteria(subject: Subject) -> str:
    """Read the stored exam-criteria Markdown for a subject."""
    return load_exam_criteria(subject)


def find_relevant_material(subject: Subject, query: str, *, vector_store=None) -> RetrievalResult:
    """Find relevant material without UI dependencies."""
    return retrieve_for_subject(subject, query, vector_store=vector_store)


def performance_summary(subject: Subject, config: AppConfig) -> dict:
    """Return the existing app-ready performance summary."""
    return subject_performance_summary(subject.key, config)


def recent_attempts(subject: Subject, config: AppConfig):
    """Return the existing recent-attempts table for Streamlit compatibility."""
    return recent_attempts_table(config, subject.key)


def _parse_learning_goals(
    text: str,
    *,
    public_subject_id: str,
    component_subject_id: str | None,
    source: Path,
    source_layer: str,
) -> list[LearningGoalRecord]:
    """Parse Markdown bullets/paragraphs into stable read-only goal records."""
    candidates: list[tuple[str, str]] = []
    current_heading = ""
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            text_value = " ".join(paragraph).strip()
            if text_value:
                candidates.append((current_heading or text_value[:80], text_value))
            paragraph.clear()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            continue
        if line.startswith("#"):
            flush_paragraph()
            current_heading = line.lstrip("#").strip()
            continue
        bullet = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)", "", line)
        if bullet != line:
            flush_paragraph()
            candidates.append((current_heading or bullet[:80], bullet))
        else:
            paragraph.append(line)
    flush_paragraph()

    records: list[LearningGoalRecord] = []
    for order, (title, goal_text) in enumerate(candidates):
        digest = hashlib.sha256(
            f"{public_subject_id}|{component_subject_id or ''}|{goal_text}".encode("utf-8")
        ).hexdigest()[:16]
        records.append(
            LearningGoalRecord(
                learning_goal_id=f"goal_{digest}",
                subject_id=public_subject_id,
                component_subject_id=component_subject_id,
                title=title,
                text=goal_text,
                order=order,
                source_name=source.name,
                source_layer=source_layer,
            )
        )
    return records


def list_learning_goals(
    config: AppConfig,
    subject_id: str,
    *,
    component_subject_id: str | None = None,
    student_id: str | None = None,
    topic: str | None = None,
) -> list[LearningGoalRecord]:
    """Read user goals when present, otherwise approved canonical goals."""
    records: list[LearningGoalRecord] = []
    for corpus_key in corpus_keys_for_request(subject_id, component_subject_id):
        subject = get_subject(corpus_key, config)
        component = corpus_key if subject_id == "spf_biology_chemistry" else None
        user_path = (
            get_user_subject_root(student_id, corpus_key, config) / "learning_goals.md"
            if student_id
            else None
        )
        if user_path and user_path.exists():
            source = user_path
            source_layer = "user_learning_goals"
        else:
            source = subject.learning_goals_file
            source_layer = "canonical_learning_goals"
        if source.exists():
            records.extend(
                _parse_learning_goals(
                    source.read_text(encoding="utf-8", errors="replace"),
                    public_subject_id=subject_id,
                    component_subject_id=component,
                    source=source,
                    source_layer=source_layer,
                )
            )
    if topic:
        needle = topic.casefold()
        records = [
            record
            for record in records
            if needle in record.title.casefold() or needle in record.text.casefold()
        ]
    return records


def subject_read_metadata(
    config: AppConfig,
    subject_id: str,
    *,
    component_subject_id: str | None = None,
    student_id: str | None = None,
) -> SubjectReadMetadata:
    """Aggregate honest material/goal metadata over resolved corpus keys."""
    corpus_keys = corpus_keys_for_request(subject_id, component_subject_id)
    materials = material_inventory(
        config,
        subject_id,
        component_subject_id=component_subject_id,
        student_id=student_id,
        include_archived=False,
    )
    goals = list_learning_goals(
        config,
        subject_id,
        component_subject_id=component_subject_id,
        student_id=student_id,
    )
    indexed_times = [item.indexed_at for item in materials if item.indexed_at is not None]
    topics = tuple(dict.fromkeys(record.title for record in goals))
    return SubjectReadMetadata(
        corpus_keys=corpus_keys,
        indexed_materials=sum(item.status == "indexed" for item in materials),
        learning_goal_count=len(goals),
        last_indexed_at=max(indexed_times) if indexed_times else None,
        topics=topics,
    )
