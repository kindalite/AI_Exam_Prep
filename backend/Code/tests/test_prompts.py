"""Tests for prompt construction."""

from __future__ import annotations

from src.prompts import build_chat_prompt, build_system_prompt
from src.subject_registry import build_subject_registry


def test_chat_prompt_contains_subject_language_sources_and_rules(temp_config) -> None:
    """Prompts should keep answers grounded in source material."""
    subject = build_subject_registry(temp_config)["spf_biology"]
    prompt = build_chat_prompt(subject, "German", "Question?", "Retrieved notes", "Goals", "Criteria")
    system_prompt = build_system_prompt(subject, "German")
    assert subject.display_name in prompt
    assert "German" in prompt
    assert "Retrieved notes" in prompt
    assert "Criteria" in prompt
    assert "Use only the provided" in system_prompt
    assert "insufficient" in system_prompt
    assert "From your materials" in system_prompt
