"""Tests for safe local image-understanding behavior."""

from __future__ import annotations

from src.image_understanding import build_study_image_description_prompt, describe_image_safe
from src.llm_client import LLMResponse


def test_image_prompt_mentions_uncertainty() -> None:
    prompt = build_study_image_description_prompt("chemistry")
    assert "Do not invent" in prompt


def test_image_understanding_safe_warning(monkeypatch, tmp_path, temp_config) -> None:
    image = tmp_path / "img.png"
    image.write_bytes(b"fake")
    monkeypatch.setattr("src.image_understanding.describe_image_with_ollama", lambda image_path, prompt, config: LLMResponse("", False, "missing model"))
    text, warning = describe_image_safe(image, "chemistry", temp_config)
    assert text == ""
    assert warning == "missing model"
