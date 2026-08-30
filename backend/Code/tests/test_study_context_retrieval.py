"""Tests for layered study context retrieval."""

from __future__ import annotations

from src.retrieval import retrieve_study_context
from src.subject_registry import build_subject_registry
from src.vector_store import InMemoryVectorStore


def test_retrieval_falls_back_to_syllabus(monkeypatch, temp_config) -> None:
    subject = build_subject_registry(temp_config)["history"]
    monkeypatch.setattr("src.syllabus_fetcher.ensure_subject_syllabus_cached", lambda subject, config: [])
    context = retrieve_study_context(
        subject,
        "scope",
        config=temp_config,
        include_syllabus=True,
        include_web=False,
        vector_store=InMemoryVectorStore(),
    )
    assert context.missing_material_detected is True
