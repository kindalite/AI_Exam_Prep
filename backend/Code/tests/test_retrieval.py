"""Tests for retrieval orchestration."""

from __future__ import annotations

from src.chunking import TextChunk
from src.retrieval import retrieve_for_subject
from src.subject_registry import build_subject_registry
from src.vector_store import InMemoryVectorStore


def test_retrieve_for_subject_returns_context(temp_config) -> None:
    """Retrieved chunks should be formatted as context for prompts."""
    subject = build_subject_registry(temp_config)["spf_biology"]
    store = InMemoryVectorStore()
    store.rebuild_collection(subject.collection_name, [TextChunk("DNA is inside the nucleus.", {"chunk_id": "1", "source_name": "bio.md"})])
    result = retrieve_for_subject(subject, "Where is DNA?", vector_store=store)
    assert "DNA" in result.context
    assert result.sources


def test_missing_collection_gives_helpful_message(temp_config) -> None:
    """Missing indexes should not crash the app."""
    subject = build_subject_registry(temp_config)["spf_biology"]
    result = retrieve_for_subject(subject, "anything", vector_store=InMemoryVectorStore())
    assert "No indexed notes" in result.message


def test_virtual_spf_parent_aggregates_component_corpora(temp_config) -> None:
    """Combined SPF retrieval queries both components without a duplicate index."""
    subjects = build_subject_registry(temp_config)
    store = InMemoryVectorStore()
    store.rebuild_collection(
        subjects["spf_biology"].collection_name,
        [TextChunk("advanced genetics", {"chunk_id": "bio", "source_name": "bio.md"})],
    )
    store.rebuild_collection(
        subjects["spf_chemistry"].collection_name,
        [TextChunk("organic molecule", {"chunk_id": "chem", "source_name": "chem.md"})],
    )
    result = retrieve_for_subject(subjects["spf_biology_chemistry"], "genetics molecule", vector_store=store)
    assert {source.metadata["chunk_id"] for source in result.sources} == {"bio", "chem"}
