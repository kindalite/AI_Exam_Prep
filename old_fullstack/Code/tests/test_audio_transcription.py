"""Tests for local audio fallback behavior."""

from __future__ import annotations

from src.audio_transcription import transcribe_audio_safe


def test_audio_missing_backend_returns_warning(monkeypatch, tmp_path, temp_config) -> None:
    audio = tmp_path / "q.wav"
    audio.write_bytes(b"fake")
    monkeypatch.setattr("src.audio_transcription.is_audio_backend_available", lambda config: False)
    text, warning = transcribe_audio_safe(audio, temp_config)
    assert text == ""
    assert "Whisper" in warning
