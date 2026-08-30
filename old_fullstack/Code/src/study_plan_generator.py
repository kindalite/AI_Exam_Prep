"""Study plan generation helpers."""

from __future__ import annotations

from .llm_client import LLMResponse, generate_response
from .prompts import build_study_plan_prompt, build_system_prompt
from .retrieval import load_learning_goals, retrieve_for_subject
from .subject_registry import Subject


def create_study_plan(subject: Subject, language: str, exam_date: str, hours_per_week: float, weak_topics: str, call_llm: bool = True) -> LLMResponse:
    """Create a study-plan prompt and optionally call the local LLM."""
    retrieved = retrieve_for_subject(subject, weak_topics or "learning goals exam revision")
    learning_goals = load_learning_goals(subject)
    prompt = build_study_plan_prompt(subject, language, exam_date, hours_per_week, weak_topics, retrieved.context, learning_goals)
    if not call_llm:
        return LLMResponse(prompt, True)
    return generate_response(prompt, build_system_prompt(subject, language))

