"""Local image-description helpers powered by Ollama when available."""

from __future__ import annotations

from pathlib import Path

from .llm_client import LLMResponse, generate_response


def build_study_image_description_prompt(subject_key: str) -> str:
    """Build the vision prompt for diagrams, handwritten notes, and page screenshots."""
    return (
        f"Describe this {subject_key} study image for retrieval. Include visible text, diagrams, labels, "
        "graphs, tables, formulas, chemistry structures, important visual relationships, and uncertainty notes. "
        "Do not invent details; say when something is unreadable."
    )


def describe_image_with_ollama(image_path: Path, prompt: str, config) -> LLMResponse:
    """Describe one local image using the configured local Ollama vision model."""
    if not image_path.exists():
        return LLMResponse("", False, f"Image file was not found: {image_path}")
    return generate_response(prompt, config=config, images=[image_path])


def describe_image_safe(image_path: Path, subject_key: str, config) -> tuple[str, str | None]:
    """Return an image description or a warning if local vision is unavailable."""
    if not getattr(config, "enable_image_understanding", True):
        return "", "Image understanding is disabled in configuration."
    response = describe_image_with_ollama(image_path, build_study_image_description_prompt(subject_key), config)
    if response.ok:
        return response.text, None
    return "", response.error or "Local vision model could not describe the image."
