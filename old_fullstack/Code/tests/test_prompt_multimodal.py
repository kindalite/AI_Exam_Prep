"""Tests for multimodal prompt content."""

from __future__ import annotations

from src.prompts import build_multimodal_chat_prompt
from src.subject_registry import build_subject_registry


def test_prompt_includes_all_context_layers(temp_config) -> None:
    subject = build_subject_registry(temp_config)["french"]
    prompt = build_multimodal_chat_prompt(subject, "French", "Question", "local", "syllabus", "web", "performance", audio_transcript="audio", image_ocr="ocr", image_description="image")
    for expected in ["Source priority rules", "local", "syllabus", "web", "performance", "French", "audio", "ocr", "image"]:
        assert expected in prompt
