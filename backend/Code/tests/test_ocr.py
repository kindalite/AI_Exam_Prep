"""Tests for OCR fallback behavior."""

from __future__ import annotations

from src.ocr import ocr_image_safe


def test_ocr_missing_file_returns_warning(tmp_path) -> None:
    text, warning = ocr_image_safe(tmp_path / "missing.png", "deu+eng+fra")
    assert text == ""
    assert "not found" in warning
