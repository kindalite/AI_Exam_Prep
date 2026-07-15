"""Quiz generation helpers that prepare prompts and optionally call the LLM."""

from __future__ import annotations

from .adaptive_learning import build_performance_context, choose_adaptive_difficulty, suggest_focus_topics
from .config import load_config
from .llm_client import LLMResponse, generate_response
from .prompts import build_quiz_prompt, build_system_prompt
from .retrieval import load_exam_criteria, retrieve_for_subject
from .subject_registry import Subject


def create_quiz(subject: Subject, language: str, learning_goal: str, difficulty: str, call_llm: bool = True) -> LLMResponse:
    """Create a quiz prompt and call the local LLM unless dry-run mode is requested."""
    config = load_config()
    topic = learning_goal or "quiz practice"
    chosen_difficulty = choose_adaptive_difficulty(subject.key, topic, config) if difficulty == "adaptive" else difficulty
    retrieved = retrieve_for_subject(subject, topic)
    criteria = load_exam_criteria(subject)
    performance_context = build_performance_context(subject.key, topic, config)
    focus_topics = suggest_focus_topics(subject.key, config)
    prompt = build_quiz_prompt(subject, language, learning_goal, chosen_difficulty, retrieved.context, criteria, performance_context, focus_topics)
    if difficulty == "adaptive":
        prompt = f"Adaptive difficulty selected: {chosen_difficulty}.\n" + prompt
    if not call_llm:
        return LLMResponse(prompt, True)
    return generate_response(prompt, build_system_prompt(subject, language), config=config)
