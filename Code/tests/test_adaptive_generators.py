"""Tests that generators accept adaptive difficulty in dry-run mode."""

from __future__ import annotations

from src.mock_exam_generator import create_mock_exam
from src.quiz_generator import create_quiz
from src.subject_registry import build_subject_registry


def test_quiz_and_mock_exam_accept_adaptive(temp_config) -> None:
    subject = build_subject_registry(temp_config)["english"]
    quiz = create_quiz(subject, "English", "grammar", "adaptive", call_llm=False)
    exam = create_mock_exam(subject, "English", 20, "adaptive", call_llm=False)
    assert quiz.ok and "Adaptive difficulty selected" in quiz.text
    assert exam.ok and "Adaptive difficulty selected" in exam.text
