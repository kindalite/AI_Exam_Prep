"""Tests for the Swiss grading formula and grader prompt."""

from __future__ import annotations

import pytest

from src.grader import calculate_grade, create_grading_feedback
from src.subject_registry import build_subject_registry


def test_grading_formula_examples() -> None:
    """Known examples protect the grading formula from accidental changes."""
    assert calculate_grade(0, 10).grade == 1
    assert calculate_grade(10, 10).grade == 6
    assert calculate_grade(5, 10).grade == 3.5


def test_invalid_points_are_rejected() -> None:
    """Impossible point values should raise a clear error."""
    with pytest.raises(ValueError):
        calculate_grade(1, 0)
    with pytest.raises(ValueError):
        calculate_grade(11, 10)


def test_create_grading_feedback_dry_run_returns_prompt(temp_config) -> None:
    """Dry-run grading should produce a prompt without calling Ollama."""
    subject = build_subject_registry(temp_config)["chemistry"]
    response = create_grading_feedback(subject, "German", "Question", "Answer", 5, call_llm=False)
    assert response.ok
    assert "Maximum points: 5" in response.text

