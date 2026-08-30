"""Tests for per-user paths and collection names."""

from __future__ import annotations

from src.user_data_paths import ensure_user_data_structure, user_memory_collection_name, user_subject_collection_name


def test_user_paths_and_collection_names_are_scoped(temp_config) -> None:
    root = ensure_user_data_structure("Alim", temp_config, ["german"])
    assert (root / "subjects" / "german" / "notes").exists()
    assert user_subject_collection_name("Alim", "german") == "user_alim__subject_german"
    assert user_memory_collection_name("Alim", "german") == "user_alim__memory_german"
