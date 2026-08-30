"""Provider-neutral runtime helpers with legacy Ollama payload compatibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from .config import AppConfig, load_config
from .model_providers import build_model_provider, build_ollama_chat_payload, get_ollama_http_session


@dataclass(frozen=True)
class ModelRuntimeStatus:
    """Current local model runtime status."""

    ok: bool
    message: str
    model: str
    server_reachable: bool
    model_available: bool


def get_ollama_session():
    """Return a reused HTTP session for Ollama calls."""
    return get_ollama_http_session()


def verify_model_runtime(config: AppConfig | None = None) -> ModelRuntimeStatus:
    """Check only the selected generation provider."""
    app_config = config or load_config()
    try:
        status = build_model_provider(app_config).status()
    except ValueError as exc:
        model = app_config.remote_llm_model or app_config.ollama_model
        return ModelRuntimeStatus(False, str(exc), model, False, False)
    return ModelRuntimeStatus(
        status.reachable,
        status.message,
        status.model,
        status.reachable,
        status.reachable,
    )


def build_chat_payload(prompt: str, system_prompt: str | None, model: str, stream: bool = False, keep_alive: str = "10m", images: list[str] | None = None) -> dict:
    """Build a chat payload with keep-alive enabled where Ollama supports it."""
    payload = build_ollama_chat_payload(
        prompt, system_prompt, model, stream=stream, images=images
    )
    payload["keep_alive"] = keep_alive
    return payload


def warm_model(config: AppConfig | None = None, timeout_seconds: int = 30) -> ModelRuntimeStatus:
    """Send a tiny non-streaming request through the selected provider."""
    app_config = config or load_config()
    status = verify_model_runtime(app_config)
    if not status.ok:
        return status
    try:
        response = build_model_provider(app_config).generate(
            "Reply with OK.", "Warm up the selected model."
        )
    except Exception as exc:
        return ModelRuntimeStatus(False, f"Model warm-up failed: {exc.__class__.__name__}", status.model, True, True)
    if not response.ok:
        return ModelRuntimeStatus(False, response.error or "Model warm-up failed.", status.model, True, True)
    return ModelRuntimeStatus(True, f"Model {status.model} warmed successfully.", status.model, True, True)


def stream_chat_tokens(config: AppConfig, payload: dict, timeout_seconds: int = 60) -> Iterator[str]:
    """Yield provider-streamed tokens from a legacy chat payload."""
    messages = payload.get("messages", [])
    system_prompt = next(
        (str(item.get("content", "")) for item in messages if item.get("role") == "system"),
        None,
    )
    prompt = next(
        (str(item.get("content", "")) for item in reversed(messages) if item.get("role") == "user"),
        "",
    )
    yield from build_model_provider(config).stream(prompt, system_prompt)
