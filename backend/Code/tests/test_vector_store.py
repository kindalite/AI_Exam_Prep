"""Tests for subject-separated vector storage."""

from __future__ import annotations

from src.chunking import TextChunk
from src.vector_store import InMemoryVectorStore


def test_in_memory_vector_store_retrieves_relevant_chunk() -> None:
    """A query should return at least one stored chunk."""
    store = InMemoryVectorStore()
    chunks = [TextChunk("cell nucleus DNA", {"chunk_id": "bio-1", "source_name": "bio.md"})]
    store.rebuild_collection("subject_biology", chunks)
    results = store.query("subject_biology", "DNA nucleus")
    assert results
    assert results[0].metadata["chunk_id"] == "bio-1"


def test_subject_collections_stay_separated() -> None:
    """A subject should not read another subject's collection."""
    store = InMemoryVectorStore()
    store.rebuild_collection("subject_biology", [TextChunk("cells", {"chunk_id": "bio"})])
    assert store.query("subject_history", "cells") == []

