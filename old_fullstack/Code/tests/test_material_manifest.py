"""Tests for material manifest change detection."""

from __future__ import annotations

from src.material_manifest import build_record, load_manifest, save_manifest_record, should_reindex


def test_manifest_detects_unchanged_and_changed_file(tmp_path) -> None:
    file_path = tmp_path / "note.md"
    file_path.write_text("one", encoding="utf-8")
    record = build_record(file_path, "german")
    manifest = tmp_path / "manifest.jsonl"
    save_manifest_record(record, manifest)
    row = load_manifest(manifest)[0]
    assert should_reindex(file_path, row) is False
    file_path.write_text("two", encoding="utf-8")
    assert should_reindex(file_path, row) is True
