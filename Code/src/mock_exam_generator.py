"""Mock exam generation helpers."""

from __future__ import annotations

from .llm_client import LLMResponse, generate_response
from .prompts import build_mock_exam_prompt, build_system_prompt
from .retrieval import load_exam_criteria, load_learning_goals, retrieve_for_subject
from .subject_registry import Subject


def create_mock_exam(subject: Subject, language: str, total_points: int, difficulty: str, call_llm: bool = True) -> LLMResponse:
    """Create a mock exam prompt and optionally send it to the local LLM."""
    query = f"mock exam {subject.display_name} {difficulty}"
    retrieved = retrieve_for_subject(subject, query)
    criteria = load_exam_criteria(subject)
    learning_goals = load_learning_goals(subject)
    prompt = build_mock_exam_prompt(subject, language, total_points, difficulty, retrieved.context, criteria, learning_goals)
    if not call_llm:
        return LLMResponse(prompt, True)
    return generate_response(prompt, build_system_prompt(subject, language))

