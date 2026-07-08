"""Tests for study plan prompt generation."""

from __future__ import annotations

from src.study_plan_generator import create_study_plan
from src.subject_registry import build_subject_registry


def test_create_study_plan_dry_run_returns_prompt(temp_config) -> None:
    """Dry-run study plans should not need a model."""
    subject = build_subject_registry(temp_config)["maths_physics"]
    response = create_study_plan(subject, "English", "2026-08-01", 4.0, "vectors", call_llm=False)
    assert response.ok
    assert "2026-08-01" in response.text
    assert "vectors" in response.text

