"""Helpers for checking and preparing the required local Ollama model."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

import requests


def is_ollama_cli_available() -> bool:
    """Return True when the ollama command is installed."""
    return shutil.which("ollama") is not None


def is_ollama_server_reachable(host: str) -> bool:
    """Return True when the local Ollama HTTP API responds."""
    try:
        response = requests.get(host.rstrip("/") + "/api/tags", timeout=5)
        return response.ok
    except requests.RequestException:
        return False


def _model_names_from_api_payload(payload: dict[str, Any]) -> list[str]:
    """Extract model names from Ollama's tag response."""
    names: list[str] = []
    for item in payload.get("models", []):
        name = item.get("name") or item.get("model")
        if name:
            names.append(str(name))
    return names


def list_ollama_models(host: str) -> list[str]:
    """List locally available Ollama models through the API, with CLI fallback."""
    try:
        response = requests.get(host.rstrip("/") + "/api/tags", timeout=8)
        if response.ok:
            return _model_names_from_api_payload(response.json())
    except (requests.RequestException, ValueError):
        pass

    if not is_ollama_cli_available():
        return []
    try:
        result = subprocess.run(["ollama", "list"], check=False, capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    names: list[str] = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if parts:
            names.append(parts[0])
    return names


def is_model_available(model_name: str, host: str) -> bool:
    """Return True when model_name is listed locally."""
    return model_name in list_ollama_models(host)


def pull_model(model_name: str, timeout_seconds: int = 1800) -> tuple[bool, str]:
    """Pull a model with the Ollama CLI and return a beginner-readable result."""
    if not is_ollama_cli_available():
        return False, "Ollama CLI is not installed. Install Ollama, then run: ollama pull gemma3:4b"
    try:
        result = subprocess.run(
            ["ollama", "pull", model_name],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return False, f"Timed out while pulling {model_name}. Try again with a longer timeout."
    except OSError as exc:
        return False, f"Could not start ollama pull: {exc}"
    output = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode == 0:
        return True, f"PASS: {model_name} was pulled or is already available."
    return False, f"FAIL: ollama pull {model_name} failed. {output}"


def ensure_required_model(config) -> tuple[bool, str]:
    """Ensure the configured required model is locally available."""
    model_name = getattr(config, "ollama_required_model", "gemma3:4b") or "gemma3:4b"
    host = getattr(config, "ollama_host", "http://localhost:11434")
    if not is_ollama_cli_available():
        return False, "FAIL: Ollama CLI is missing. Install Ollama, then run: ollama pull gemma3:4b"
    if not is_ollama_server_reachable(host):
        return False, f"FAIL: Ollama server is not reachable at {host}. Start Ollama and retry."
    if is_model_available(model_name, host):
        return True, f"PASS: required local model {model_name} is available."
    auto_pull = bool(getattr(config, "auto_pull_ollama_model", False))
    allow_download = bool(getattr(config, "allow_model_download", False))
    if not (auto_pull and allow_download):
        return False, f"FAIL: {model_name} is missing. Run: ollama pull {model_name}"
    ok, message = pull_model(model_name, int(getattr(config, "model_download_timeout_seconds", 1800)))
    if not ok:
        return False, message
    if is_model_available(model_name, host):
        return True, f"PASS: required local model {model_name} is available after pull."
    return False, f"FAIL: {model_name} was pulled but did not appear in ollama list."
