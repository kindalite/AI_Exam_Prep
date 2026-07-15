"""Tests for multimodal PDF metadata using mocks."""

from __future__ import annotations

from pathlib import Path

from src.multimodal_pdf import load_pdf_multimodal


def test_multimodal_pdf_returns_modalities(monkeypatch, tmp_path, temp_config) -> None:
    pdf = tmp_path / "sample.pdf"
    pdf.write_bytes(b"fake")
    image = tmp_path / "page.png"
    image.write_bytes(b"image")
    monkeypatch.setattr("src.multimodal_pdf._load_selectable_text", lambda path, subject: [])
    monkeypatch.setattr("src.multimodal_pdf._page_count", lambda path, fallback: 1)
    monkeypatch.setattr("src.multimodal_pdf.render_pdf_page_to_image", lambda path, page, out, dpi: image)
    monkeypatch.setattr("src.multimodal_pdf.ocr_image_safe", lambda path, languages: ("OCR text", None))
    monkeypatch.setattr("src.multimodal_pdf.describe_image_safe", lambda path, subject, config: ("Image description", None))
    monkeypatch.setattr("src.multimodal_pdf.extract_embedded_images", lambda path, out: [])
    docs = load_pdf_multimodal(pdf, "spf_biology", temp_config)
    modalities = {doc.metadata["modality"] for doc in docs}
    assert {"ocr_text", "page_image_description"}.issubset(modalities)
    assert docs[0].metadata["page_number"] == 1
