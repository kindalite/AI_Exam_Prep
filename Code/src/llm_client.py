"""Local LLM client for Ollama with graceful error handling."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

import requests

from .config import AppConfig, load_config
from .token_budget import assert_prompt_under_limit


@dataclass(frozen=True)
class LLMResponse:
    """The result of asking the local language model for text."""

    text: str
    ok: bool
    error: str | None = None


def _encode_image(path: Path) -> str:
    """Encode a local image for Ollama's multimodal chat API."""
    return base64.b64encode(path.read_bytes()).decode("ascii")


def build_ollama_payload(prompt: str, system_prompt: str | None, model: str, images: list[Path] | None = None) -> dict:
    """Build the JSON payload expected by Ollama's chat API."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    user_message: dict = {"role": "user", "content": prompt}
    if images:
        user_message["images"] = [_encode_image(Path(image)) for image in images]
    messages.append(user_message)
    return {"model": model, "messages": messages, "stream": False}


def _missing_model_message(model: str) -> str:
    """Return the required actionable missing-model message."""
    return f"The required local model {model} is not available. Run: ollama pull {model}"


def generate_response(
    prompt: str,
    system_prompt: str | None = None,
    config: AppConfig | None = None,
    images: list[Path] | None = None,
) -> LLMResponse:
    """Generate a local response with Ollama gemma3:4b, optionally with local images."""
    app_config = config or load_config()
    if app_config.model_provider.lower() != "ollama":
        return LLMResponse("", False, "Only the local Ollama provider is implemented. Cloud LLM APIs are not used.")
    if not app_config.ollama_host:
        return LLMResponse("", False, "OLLAMA_HOST is missing. Set it in .env.")

    model = app_config.ollama_vision_model if images else app_config.ollama_model
    url = app_config.ollama_host.rstrip("/") + "/api/chat"
    try:
        assert_prompt_under_limit((system_prompt or "") + "\n" + prompt, app_config)
    except ValueError as exc:
        return LLMResponse("", False, f"Prompt is too large for the local 128K context window: {exc}")
    try:
        payload = build_ollama_payload(prompt, system_prompt, model, images=images)
    except OSError as exc:
        return LLMResponse("", False, f"Could not read local image for Ollama: {exc}")
    try:
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 404:
            return LLMResponse("", False, _missing_model_message(model))
        response.raise_for_status()
        data = response.json()
        return LLMResponse(data.get("message", {}).get("content", ""), True)
    except requests.RequestException as exc:
        message = str(exc)
        if "model" in message.lower() or "404" in message:
            return LLMResponse("", False, _missing_model_message(model))
        return LLMResponse("", False, f"Ollama could not be reached locally at {app_config.ollama_host}: {exc}")
    except ValueError as exc:
        return LLMResponse("", False, f"Ollama returned invalid JSON: {exc}")
