"""Tests for local Ollama model checks without real Ollama."""

from __future__ import annotations

from pathlib import Path

from src.config import load_config
from src.ollama_model_manager import ensure_required_model, is_model_available


def test_config_defaults_use_gemma() -> None:
    config = load_config(Path(__file__).resolve().parents[1])
    assert config.ollama_model == "gemma3:4b"
    assert config.ollama_required_model == "gemma3:4b"


def test_missing_ollama_cli_does_not_crash(monkeypatch, temp_config) -> None:
    monkeypatch.setattr("src.ollama_model_manager.shutil.which", lambda _name: None)
    ok, message = ensure_required_model(temp_config)
    assert ok is False
    assert "Ollama CLI" in message


def test_mocked_available_model(monkeypatch, temp_config) -> None:
    monkeypatch.setattr("src.ollama_model_manager.list_ollama_models", lambda _host: ["gemma3:4b"])
    assert is_model_available("gemma3:4b", temp_config.ollama_host)


def test_pull_path_when_missing_and_allowed(monkeypatch, temp_config) -> None:
    calls = []
    monkeypatch.setattr("src.ollama_model_manager.is_ollama_cli_available", lambda: True)
    monkeypatch.setattr("src.ollama_model_manager.is_ollama_server_reachable", lambda _host: True)
    monkeypatch.setattr("src.ollama_model_manager.list_ollama_models", lambda _host: ["gemma3:4b"] if calls else [])
    monkeypatch.setattr("src.ollama_model_manager.pull_model", lambda model, timeout: calls.append((model, timeout)) or (True, "pulled"))
    ok, _message = ensure_required_model(temp_config)
    assert ok is True
    assert calls[0][0] == "gemma3:4b"
