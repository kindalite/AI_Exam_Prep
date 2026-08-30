"""Tests for loading local study documents."""

from __future__ import annotations

from pathlib import Path

from src.document_loaders import load_document


def test_load_markdown_file() -> None:
    """Markdown notes should load with source metadata."""
    path = Path("test_data/biology_sample.md")
    documents = load_document(path, "biology")
    assert documents[0].text.startswith("# Biology Sample")
    assert documents[0].metadata["source_name"] == "biology_sample.md"
    assert documents[0].metadata["subject"] == "biology"
    assert documents[0].metadata["source_type"] == "md"


def test_load_text_file(tmp_path: Path) -> None:
    """Plain text notes should load like Markdown notes."""
    path = tmp_path / "note.txt"
    path.write_text("A short note.", encoding="utf-8")
    documents = load_document(path, "history")
    assert documents[0].text == "A short note."
    assert documents[0].metadata["source_type"] == "txt"

