"""Tests for readable text chunking."""

from __future__ import annotations

from src.chunking import chunk_text


def test_short_text_returns_one_chunk() -> None:
    """Short notes should stay in one chunk."""
    chunks = chunk_text("short text", {"source_name": "note.md"}, chunk_size=50, overlap=5)
    assert len(chunks) == 1


def test_long_text_returns_multiple_chunks_and_preserves_overlap() -> None:
    """Long notes should split while keeping overlap for context."""
    text = "abcdefghijklmnopqrstuvwxyz" * 5
    chunks = chunk_text(text, {"source_name": "letters.md"}, chunk_size=40, overlap=10)
    assert len(chunks) > 1
    assert chunks[0].text[-10:] == chunks[1].text[:10]


def test_empty_text_returns_empty_list() -> None:
    """Empty files should not create empty vector entries."""
    assert chunk_text("   ", {"source_name": "empty.md"}) == []

