"""Local LLM client for Ollama with graceful error handling."""

from __future__ import annotations

import base64
from pathlib import Path

from .config import AppConfig, load_config
from .model_providers import GenerationProvider, build_model_provider, build_ollama_chat_payload
from .model_types import LLMResponse
from .performance_monitor import measure_operation
from .token_budget import assert_prompt_under_limit


def _encode_image(path: Path) -> str:
    """Encode a local image for Ollama's multimodal chat API."""
    return base64.b64encode(path.read_bytes()).decode("ascii")


def build_ollama_payload(prompt: str, system_prompt: str | None, model: str, images: list[Path] | None = None, stream: bool = False) -> dict:
    """Build the JSON payload expected by Ollama's chat API."""
    encoded_images = [_encode_image(Path(image)) for image in images] if images else None
    return build_ollama_chat_payload(
        prompt, system_prompt, model, stream=stream, images=encoded_images
    )


def _missing_model_message(model: str) -> str:
    """Return the required actionable missing-model message."""
    return f"The required local model {model} is not available. Run: ollama pull {model}"


def generate_response(
    prompt: str,
    system_prompt: str | None = None,
    config: AppConfig | None = None,
    images: list[Path] | None = None,
    provider: GenerationProvider | None = None,
) -> LLMResponse:
    """Generate through the selected provider while preserving the legacy seam."""
    app_config = config or load_config()
    try:
        assert_prompt_under_limit((system_prompt or "") + "\n" + prompt, app_config)
    except ValueError as exc:
        return LLMResponse("", False, f"Prompt is too large for the local 128K context window: {exc}")
    try:
        selected = provider or build_model_provider(app_config)
    except ValueError as exc:
        return LLMResponse("", False, str(exc))
    model = (
        app_config.ollama_vision_model if images and app_config.model_provider == "ollama"
        else app_config.ollama_model if app_config.model_provider == "ollama"
        else app_config.remote_llm_model
    )
    with measure_operation(app_config, f"{app_config.model_provider}_chat", model):
        return selected.generate(prompt, system_prompt, images=images)
