"""Tests for the subject registry."""

from __future__ import annotations

import pytest

from src.subject_languages import language_for_api_subject, language_instruction
from src.subject_registry import (
    COMPONENT_SUBJECT_IDS,
    TOP_LEVEL_SUBJECT_IDS,
    build_subject_registry,
    corpus_keys_for_request,
    subjects_for_display,
    validate_component_for_subject,
    validate_top_level_subject_id,
)


def test_required_subjects_exist(temp_config) -> None:
    """Every required subject should be available in the selector."""
    subjects = build_subject_registry(temp_config)
    displayed = subjects_for_display(temp_config)
    assert tuple(subject.key for subject in displayed) == TOP_LEVEL_SUBJECT_IDS
    assert len(displayed) == 15
    assert all(subject.is_top_level for subject in displayed)
    assert set(COMPONENT_SUBJECT_IDS).issubset(subjects)
    assert not any(component in {subject.key for subject in displayed} for component in COMPONENT_SUBJECT_IDS)


def test_subjects_have_paths_and_collection_names(temp_config) -> None:
    """Each subject needs paths and collection names for RAG separation."""
    for subject in build_subject_registry(temp_config).values():
        assert subject.collection_name
        assert subject.default_language
        assert subject.notes_dir.name == "notes"
        assert subject.learning_goals_file.name == "learning_goals.md"
        assert subject.exam_criteria_file.name == "exam_criteria.md"


def test_spf_parent_and_component_validation(temp_config) -> None:
    """The virtual SPF parent routes to one or both concrete component corpora."""
    subjects = build_subject_registry(temp_config)
    parent = subjects["spf_biology_chemistry"]
    assert parent.is_virtual
    assert parent.components == COMPONENT_SUBJECT_IDS
    assert corpus_keys_for_request(parent.key) == COMPONENT_SUBJECT_IDS
    assert corpus_keys_for_request(parent.key, "spf_biology") == ("spf_biology",)
    assert validate_component_for_subject(parent.key, "spf_chemistry") == "spf_chemistry"
    with pytest.raises(ValueError):
        validate_top_level_subject_id("spf_biology")
    with pytest.raises(ValueError):
        validate_component_for_subject("biology", "spf_biology")


def test_api_language_contract() -> None:
    """Each API subject has a stable code and precise instruction."""
    assert language_for_api_subject("mathematics") == "en"
    assert language_for_api_subject("french") == "fr"
    assert language_for_api_subject("economics") == "de"
    assert "Grade-11" in language_instruction("en")
    assert "CEFR B1" in language_instruction("fr")
    assert "Swiss Gymnasium" in language_instruction("de")
