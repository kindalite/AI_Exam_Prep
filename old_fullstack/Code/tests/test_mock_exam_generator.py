"""Tests for mock exam prompt generation."""

from __future__ import annotations

from src.mock_exam_generator import create_mock_exam
from src.subject_registry import build_subject_registry


def test_create_mock_exam_dry_run_returns_prompt(temp_config) -> None:
    """Dry-run mock exams should build a full prompt without Ollama."""
    subject = build_subject_registry(temp_config)["history"]
    response = create_mock_exam(subject, "English", 30, "medium", call_llm=False)
    assert response.ok
    assert "Total points: 30" in response.text
    assert "marking scheme" in response.text

