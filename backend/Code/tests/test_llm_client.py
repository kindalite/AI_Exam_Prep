"""Tests for the Ollama client without calling a real model."""

from __future__ import annotations

from pathlib import Path

from src.config import AppConfig
from src.llm_client import build_ollama_payload, generate_response


def test_ollama_payload_contains_model_and_messages() -> None:
    """The payload should match Ollama's chat structure."""
    payload = build_ollama_payload("Hello", "System", "model-name")
    assert payload["model"] == "model-name"
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["content"] == "Hello"


def test_missing_host_returns_readable_error(tmp_path: Path) -> None:
    """A missing host should return a friendly error, not crash."""
    config = AppConfig(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        subject_data_dir=tmp_path / "data" / "subjects",
        vector_db_dir=tmp_path / "vector_db",
        feedback_file=tmp_path / "feedback.jsonl",
        stats_file=tmp_path / "grades.csv",
        model_provider="ollama",
        ollama_host="",
        ollama_model="test",
        embedding_model="test",
        chunk_size=100,
        chunk_overlap=10,
    )
    response = generate_response("prompt", config=config)
    assert response.ok is False
    assert "OLLAMA_HOST" in response.error


def test_provider_defaults_to_ollama(temp_config) -> None:
    """The MVP should default to local Ollama."""
    assert temp_config.model_provider == "ollama"

