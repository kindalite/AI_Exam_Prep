"""Focused quiz-mode helpers for generation and timed attempts."""

from __future__ import annotations

from .quiz_generator import create_quiz
from .timed_practice import start_practice_attempt


def generate_quiz_set(subject, language: str, learning_goal: str, difficulty: str, number_of_questions: int, include_syllabus: bool = True, include_web: bool = False, call_llm: bool = True):
    """Generate a quiz set prompt/response for quiz mode."""
    response = create_quiz(subject, language, f"{learning_goal}\nNumber of questions: {number_of_questions}", difficulty, call_llm=call_llm)
    return response


def start_quiz_mode(user_id: str, subject, language: str, topic: str, difficulty_requested: str, difficulty_used: str, timer_minutes: int, generated_text: str, config):
    """Persist a generated quiz and start the timed quiz session."""
    return start_practice_attempt(user_id, subject.key, "quiz", language, topic, difficulty_requested, difficulty_used, timer_minutes, generated_text, config)
