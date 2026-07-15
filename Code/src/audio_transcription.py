"""Local audio transcription helpers with graceful missing-backend behavior."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def is_audio_backend_available(config) -> bool:
    """Return True when the configured local audio backend can be imported."""
    backend = getattr(config, "audio_transcription_backend", "whisper_local")
    if backend != "whisper_local":
        return False
    return importlib.util.find_spec("faster_whisper") is not None


def transcribe_audio_safe(audio_path: Path, config) -> tuple[str, str | None]:
    """Transcribe audio locally or return a clear warning."""
    if not getattr(config, "enable_audio_input", True):
        return "", "Audio input is disabled in configuration."
    if not audio_path.exists():
        return "", f"Audio file was not found: {audio_path}"
    if not is_audio_backend_available(config):
        return "", "Local Whisper backend is unavailable. Install faster-whisper and ffmpeg, or type the question."
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel(getattr(config, "whisper_model_size", "base"), device="cpu", compute_type="int8")
        segments, _info = model.transcribe(str(audio_path))
        return " ".join(segment.text.strip() for segment in segments).strip(), None
    except Exception as exc:  # noqa: BLE001 - optional backend boundary.
        return "", f"Audio transcription failed locally: {exc}"
