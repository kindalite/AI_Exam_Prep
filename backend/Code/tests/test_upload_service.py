"""Focused tests for streamed user-scoped upload and indexing orchestration."""

from __future__ import annotations

from dataclasses import replace
from io import BytesIO

import pytest

from src.document_loaders import LoadedDocument
from src.material_manifest import load_manifest
from src.services.identity_service import StudentContext
from src.services.upload_service import (
    DocumentParseError,
    FileTooLargeError,
    IndexBusyError,
    IndexLockRegistry,
    UnsupportedMediaTypeError,
    import_student_document,
)
from src.user_data_paths import get_user_subject_root
from src.vector_store import InMemoryVectorStore


def _import(temp_config, student="student-a", **updates):
    values = {
        "stream": BytesIO(b"# Notes\n\nMitochondria produce ATP."),
        "original_name": "biology.md",
        "content_type": "text/markdown",
        "subject_id": "biology",
        "component_subject_id": None,
        "section": "cells",
        "language": "de",
        "student": StudentContext(student),
        "config": temp_config,
        "vector_store": InMemoryVectorStore(),
    }
    values.update(updates)
    return import_student_document(**values)


def test_markdown_upload_streams_persists_metadata_and_indexes(temp_config) -> None:
    """Accepted content is stored under the user root with filterable metadata."""
    store = InMemoryVectorStore()
    result = _import(temp_config, vector_store=store)
    assert result.status == "indexed"
    assert result.chunks_indexed > 0
    assert result.pages is None
    root = get_user_subject_root("student-a", "biology", temp_config)
    stored = list((root / "notes").glob(f"{result.material_id}__*.md"))
    assert len(stored) == 1
    manifest = load_manifest(root / "material_manifest.jsonl")
    assert manifest[0]["material_id"] == result.material_id
    assert manifest[0]["original_name"] == "biology.md"
    assert manifest[0]["status"] == "indexed"

    chunks = store.query(
        "user_student-a__subject_biology",
        "ATP",
        where={"user_id": "student-a"},
    )
    assert chunks and chunks[0].metadata["material_id"] == result.material_id


def test_upload_limits_media_validation_parse_review_and_warnings(temp_config) -> None:
    """Rejected/partial files produce the documented safe outcomes."""
    with pytest.raises(FileTooLargeError):
        _import(temp_config, config=replace(temp_config, max_upload_bytes=3))
    with pytest.raises(UnsupportedMediaTypeError):
        _import(temp_config, original_name="payload.exe", content_type="application/octet-stream")

    def broken_loader(*args, **kwargs):
        raise ValueError("malformed")

    with pytest.raises(DocumentParseError):
        _import(
            temp_config,
            original_name="broken.pdf",
            content_type="application/pdf",
            loader=broken_loader,
        )
    root = get_user_subject_root("student-a", "biology", temp_config)
    assert any(row["status"] == "needs_review" for row in load_manifest(root / "material_manifest.jsonl"))

    def warning_loader(path, subject_key, config):
        return [
            LoadedDocument(
                "partial OCR text",
                {"source_name": path.name, "ocr_warning": "OCR language missing"},
            )
        ]

    warned = _import(
        temp_config,
        original_name="scan.png",
        content_type="image/png",
        loader=warning_loader,
        indexer=lambda *args, **kwargs: 1,
    )
    assert warned.status == "indexed"
    assert warned.warnings == ("OCR language missing",)


def test_spf_requires_component_busy_lock_and_student_ids_are_isolated(temp_config) -> None:
    """Private SPF uploads are singular and full rebuilds cannot overlap."""
    with pytest.raises(ValueError, match="component_subject_id"):
        _import(
            temp_config,
            subject_id="spf_biology_chemistry",
            component_subject_id=None,
        )

    locks = IndexLockRegistry()
    with locks.hold("student-a:biology"):
        with pytest.raises(IndexBusyError):
            _import(temp_config, locks=locks)

    first = _import(temp_config, student="student-a")
    second = _import(temp_config, student="student-b")
    assert first.material_id != second.material_id
    assert get_user_subject_root("student-a", "biology", temp_config) != get_user_subject_root(
        "student-b", "biology", temp_config
    )
