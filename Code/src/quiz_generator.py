"""Quiz generation helpers that prepare prompts and optionally call the LLM."""

from __future__ import annotations

from .llm_client import LLMResponse, generate_response
from .prompts import build_quiz_prompt, build_system_prompt
from .retrieval import load_exam_criteria, retrieve_for_subject
from .subject_registry import Subject


def create_quiz(subject: Subject, language: str, learning_goal: str, difficulty: str, call_llm: bool = True) -> LLMResponse:
    """Create a quiz prompt and call the local LLM unless dry-run mode is requested."""
    retrieved = retrieve_for_subject(subject, learning_goal or "quiz practice")
    criteria = load_exam_criteria(subject)
    prompt = build_quiz_prompt(subject, language, learning_goal, difficulty, retrieved.context, criteria)
    if not call_llm:
        return LLMResponse(prompt, True)
    return generate_response(prompt, build_system_prompt(subject, language))

