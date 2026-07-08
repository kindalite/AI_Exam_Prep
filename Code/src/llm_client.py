"""Local LLM client for Ollama with graceful error handling."""

from __future__ import annotations

from dataclasses import dataclass

import requests

from .config import AppConfig, load_config


@dataclass(frozen=True)
class LLMResponse:
    """The result of asking the local language model for text."""

    text: str
    ok: bool
    error: str | None = None


def build_ollama_payload(prompt: str, system_prompt: str | None, model: str) -> dict:
    """Build the JSON payload expected by Ollama's chat API."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    return {"model": model, "messages": messages, "stream": False}


def generate_response(prompt: str, system_prompt: str | None = None, config: AppConfig | None = None) -> LLMResponse:
    """Call Ollama and return either generated text or a readable error."""
    app_config = config or load_config()
    if app_config.model_provider.lower() != "ollama":
        return LLMResponse("", False, "Only the local Ollama provider is implemented in this MVP.")
    if not app_config.ollama_host:
        return LLMResponse("", False, "OLLAMA_HOST is missing. Set it in .env.")

    url = app_config.ollama_host.rstrip("/") + "/api/chat"
    payload = build_ollama_payload(prompt, system_prompt, app_config.ollama_model)
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return LLMResponse(data.get("message", {}).get("content", ""), True)
    except requests.RequestException as exc:
        return LLMResponse(
            "",
            False,
            f"Ollama could not be reached or the model is missing: {exc}",
        )
    except ValueError as exc:
        return LLMResponse("", False, f"Ollama returned invalid JSON: {exc}")

