"""Tests for the subject registry."""

from __future__ import annotations

from src.subject_registry import build_subject_registry


def test_required_subjects_exist(temp_config) -> None:
    """Every required subject should be available in the selector."""
    subjects = build_subject_registry(temp_config)
    required_display_names = {
        "SPF Chemistry",
        "SPF Biology",
        "Political Education",
        "Philosophy",
        "Pedagogics/Psychology",
        "Maths/Physics",
        "History",
        "German",
        "French",
        "English",
        "Chemistry",
    }
    assert {subject.display_name for subject in subjects.values()} == required_display_names


def test_subjects_have_paths_and_collection_names(temp_config) -> None:
    """Each subject needs paths and collection names for RAG separation."""
    for subject in build_subject_registry(temp_config).values():
        assert subject.collection_name
        assert subject.default_language
        assert subject.notes_dir.name == "notes"
        assert subject.learning_goals_file.name == "learning_goals.md"
        assert subject.exam_criteria_file.name == "exam_criteria.md"

