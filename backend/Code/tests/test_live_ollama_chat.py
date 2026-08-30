"""Explicitly opt-in live Ollama smoke coverage for API chat."""

from __future__ import annotations

import os

import pytest

from src.services.chat_service import run_api_chat
from src.services.identity_service import StudentContext
from src.vector_store import InMemoryVectorStore


@pytest.mark.skipif(
    os.getenv("RUN_LIVE_OLLAMA_CHAT") != "1",
    reason="Set RUN_LIVE_OLLAMA_CHAT=1 to call the configured local Ollama model.",
)
def test_live_ollama_non_streaming_chat(temp_config) -> None:
    """Call local Ollama only when a developer explicitly opts in."""
    result = run_api_chat(
        subject_id="history",
        component_subject_id=None,
        language="en",
        question="In one sentence, explain why primary sources matter in history.",
        learning_goal_id=None,
        material_ids=[],
        top_k=2,
        student=StudentContext("live-smoke-student"),
        config=temp_config,
        vector_store=InMemoryVectorStore(),
    )
    assert result.answer.strip()
    assert result.used_model == temp_config.ollama_model
