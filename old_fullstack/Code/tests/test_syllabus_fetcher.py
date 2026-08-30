"""Tests for syllabus extraction using mocked sources."""

from __future__ import annotations

from src.syllabus_fetcher import extract_subject_syllabus_sections, subject_to_syllabus_keywords
from src.subject_registry import build_subject_registry
from src.web_retrieval import WebSource


def test_syllabus_extracts_relevant_subject_section(temp_config) -> None:
    subject = build_subject_registry(temp_config)["chemistry"]
    source = WebSource("KSA", "https://example.test", "Chemie Lehrplan 4. Klasse", "Chemie", "now", "html")
    docs = extract_subject_syllabus_sections(subject, [source])
    assert docs
    assert docs[0].metadata["source_layer"] == "official_syllabus"
    assert "chemie" in subject_to_syllabus_keywords(subject)
