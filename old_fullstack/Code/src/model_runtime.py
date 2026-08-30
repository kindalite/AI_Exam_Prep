"""Ollama runtime helpers for warm-up, keep-alive, streaming, and reuse."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterator

import requests

from .config import AppConfig, load_config
from .ollama_model_manager import is_model_available, is_ollama_server_reachable


@dataclass(frozen=True)
class ModelRuntimeStatus:
    """Current local model runtime status."""

    ok: bool
    message: str
    model: str
    server_reachable: bool
    model_available: bool


_SESSION: requests.Session | None = None


def get_ollama_session() -> requests.Session:
    """Return a reused HTTP session for Ollama calls."""
    global _SESSION
    if _SESSION is None:
        _SESSION = requests.Session()
    return _SESSION


def verify_model_runtime(config: AppConfig | None = None) -> ModelRuntimeStatus:
    """Check Ollama server and required gemma3:4b availability."""
    app_config = config or load_config()
    model = app_config.ollama_required_model or app_config.ollama_model
    server_ok = is_ollama_server_reachable(app_config.ollama_host)
    model_ok = is_model_available(model, app_config.ollama_host) if server_ok else False
    if not server_ok:
        return ModelRuntimeStatus(False, f"Ollama is not reachable at {app_config.ollama_host}. Start Ollama first.", model, False, False)
    if not model_ok:
        return ModelRuntimeStatus(False, f"Required local model {model} is not available. Run: ollama pull {model}", model, True, False)
    return ModelRuntimeStatus(True, f"Local Ollama model {model} is ready.", model, True, True)


def build_chat_payload(prompt: str, system_prompt: str | None, model: str, stream: bool = False, keep_alive: str = "10m", images: list[str] | None = None) -> dict:
    """Build a chat payload with keep-alive enabled where Ollama supports it."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    user_message: dict = {"role": "user", "content": prompt}
    if images:
        user_message["images"] = images
    messages.append(user_message)
    return {"model": model, "messages": messages, "stream": stream, "keep_alive": keep_alive}


def warm_model(config: AppConfig | None = None, timeout_seconds: int = 30) -> ModelRuntimeStatus:
    """Send a tiny request to keep the local model warm."""
    app_config = config or load_config()
    status = verify_model_runtime(app_config)
    if not status.ok:
        return status
    payload = build_chat_payload("Reply with OK.", "Warm up the local model.", status.model, stream=False)
    try:
        response = get_ollama_session().post(app_config.ollama_host.rstrip("/") + "/api/chat", json=payload, timeout=timeout_seconds)
        response.raise_for_status()
    except requests.RequestException as exc:
        return ModelRuntimeStatus(False, f"Model warm-up failed: {exc}", status.model, True, True)
    return ModelRuntimeStatus(True, f"Model {status.model} warmed successfully.", status.model, True, True)


def stream_chat_tokens(config: AppConfig, payload: dict, timeout_seconds: int = 60) -> Iterator[str]:
    """Yield streamed Ollama tokens from a chat payload."""
    stream_payload = dict(payload)
    stream_payload["stream"] = True
    response = get_ollama_session().post(config.ollama_host.rstrip("/") + "/api/chat", json=stream_payload, timeout=timeout_seconds, stream=True)
    response.raise_for_status()
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            data = json.loads(line)
        except ValueError:
            continue
        content = data.get("message", {}).get("content", "")
        if content:
            yield content
