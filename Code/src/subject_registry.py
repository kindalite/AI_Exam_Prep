"""Subject registry with paths, language defaults, and study instructions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig, load_config
from .utils import ensure_directory, write_text_if_missing


@dataclass(frozen=True)
class Subject:
    """Configuration for one school subject."""

    key: str
    display_name: str
    default_language: str
    notes_dir: Path
    syllabus_dir: Path
    criteria_dir: Path
    learning_goals_file: Path
    exam_criteria_file: Path
    collection_name: str
    instructions: str


SUBJECT_DEFINITIONS: tuple[tuple[str, str, str, str], ...] = (
    ("spf_chemistry", "SPF Chemistry", "German", "Analyze exercises, create similar tasks, answer current-topic questions, and describe simple molecules."),
    ("spf_biology", "SPF Biology", "German", "Analyze biology material and answer from pages, PDFs, notes, syllabus, and criteria."),
    ("political_education", "Political Education", "German", "Analyze political education material and connect answers to course criteria."),
    ("philosophy", "Philosophy", "German", "Explain arguments clearly and connect ideas to the treated material."),
    ("pedagogics_psychology", "Pedagogics/Psychology", "German", "Use course concepts to analyze examples and answer exam-style questions."),
    ("maths_physics", "Maths/Physics", "English", "Generate similar problems, show correct methods, and include final answers."),
    ("history", "History", "English", "Place events and texts in historical context and test all given material."),
    ("german", "German", "German", "Create vocabulary quizlets, class-style literature questions, and writing feedback."),
    ("french", "French", "French", "Use simple B1 French for vocabulary, grammar explanations, and similar exercises."),
    ("english", "English", "English", "Analyze grammar exercises and books, then create class-style questions."),
    ("chemistry", "Chemistry", "German", "Stay inside class scope and explain concepts, graphics, and simple molecule descriptions."),
)


def build_subject_registry(config: AppConfig | None = None) -> dict[str, Subject]:
    """Create all subject configurations from the current app settings."""
    app_config = config or load_config()
    subjects: dict[str, Subject] = {}
    for key, display_name, language, instructions in SUBJECT_DEFINITIONS:
        subject_dir = app_config.subject_data_dir / key
        subjects[key] = Subject(
            key=key,
            display_name=display_name,
            default_language=language,
            notes_dir=subject_dir / "notes",
            syllabus_dir=subject_dir / "syllabus",
            criteria_dir=subject_dir / "criteria",
            learning_goals_file=subject_dir / "learning_goals.md",
            exam_criteria_file=subject_dir / "exam_criteria.md",
            collection_name=f"subject_{key}",
            instructions=instructions,
        )
    return subjects


def get_subject(subject_key: str, config: AppConfig | None = None) -> Subject:
    """Return one subject or raise a helpful KeyError if it does not exist."""
    subjects = build_subject_registry(config)
    if subject_key not in subjects:
        raise KeyError(f"Unknown subject key: {subject_key}")
    return subjects[subject_key]


def setup_subject_folders(config: AppConfig | None = None) -> None:
    """Create subject folders and starter files for a new local project."""
    for subject in build_subject_registry(config).values():
        ensure_directory(subject.notes_dir)
        ensure_directory(subject.syllabus_dir)
        ensure_directory(subject.criteria_dir)
        write_text_if_missing(
            subject.learning_goals_file,
            f"# Learning Goals: {subject.display_name}\n\nAdd exam learning goals here.\n",
        )
        write_text_if_missing(
            subject.exam_criteria_file,
            f"# Exam Criteria: {subject.display_name}\n\nAdd teacher criteria and grading expectations here.\n",
        )


def subjects_for_display(config: AppConfig | None = None) -> list[Subject]:
    """Return subjects sorted by display name for the Streamlit selector."""
    return sorted(build_subject_registry(config).values(), key=lambda item: item.display_name)

