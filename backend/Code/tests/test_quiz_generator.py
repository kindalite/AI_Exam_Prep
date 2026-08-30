"""Tests for quiz prompt generation."""

from __future__ import annotations

from src.quiz_generator import create_quiz
from src.subject_registry import build_subject_registry


def test_create_quiz_dry_run_returns_prompt(temp_config) -> None:
    """Dry-run quiz generation should not require Ollama."""
    subject = build_subject_registry(temp_config)["french"]
    response = create_quiz(subject, "French", "vocabulaire", "easy", call_llm=False)
    assert response.ok
    assert "quiz" in response.text.lower()
    assert "French" in response.text

