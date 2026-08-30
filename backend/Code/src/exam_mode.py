"""Focused exam-mode helpers for generation and timed attempts."""

from __future__ import annotations

from .mock_exam_generator import create_mock_exam
from .timed_practice import start_practice_attempt


def generate_exam_set(subject, language: str, total_points: int, difficulty: str, call_llm: bool = True):
    """Generate an exam question set prompt/response for exam mode."""
    return create_mock_exam(subject, language, total_points, difficulty, call_llm=call_llm)


def start_exam_mode(user_id: str, subject, language: str, topic: str, difficulty_requested: str, difficulty_used: str, timer_minutes: int, generated_text: str, config):
    """Persist a generated exam and start the timed exam session."""
    return start_practice_attempt(user_id, subject.key, "exam", language, topic, difficulty_requested, difficulty_used, timer_minutes, generated_text, config)
