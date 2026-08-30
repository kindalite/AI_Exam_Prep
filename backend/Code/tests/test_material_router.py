"""Tests for discovering and grouping learning material."""

from __future__ import annotations

from dataclasses import replace

from src.material_router import discover_learning_material, group_material_by_subject
from src.subject_registry import build_subject_registry


def test_material_router_finds_and_groups_files(tmp_path, temp_config) -> None:
    root = tmp_path / "learning_material"
    (root / "Biologie").mkdir(parents=True)
    file_path = root / "Biologie" / "cells.pdf"
    file_path.write_text("fake", encoding="utf-8")
    config = replace(temp_config, learning_material_root=root)
    subjects = build_subject_registry(config)
    paths = discover_learning_material(config)
    grouped = group_material_by_subject(paths, subjects)
    assert file_path in paths
    assert grouped["biology"] == [file_path]


def test_material_router_preserves_spf_and_legacy_combined_folders(tmp_path, temp_config) -> None:
    """SPF folders stay components and legacy Maths & Physics remains readable."""
    root = tmp_path / "learning_material"
    (root / "SPF Biology").mkdir(parents=True)
    (root / "Maths & Physics").mkdir(parents=True)
    spf_file = root / "SPF Biology" / "advanced.pdf"
    legacy_file = root / "Maths & Physics" / "mechanics.pdf"
    spf_file.write_text("fake", encoding="utf-8")
    legacy_file.write_text("fake", encoding="utf-8")
    config = replace(temp_config, learning_material_root=root)
    grouped = group_material_by_subject(discover_learning_material(config), build_subject_registry(config))
    assert grouped["spf_biology"] == [spf_file]
    assert legacy_file in grouped["mathematics"]
    assert legacy_file in grouped["physics"]
