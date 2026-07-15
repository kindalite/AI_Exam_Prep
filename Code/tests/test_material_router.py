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
    assert grouped["spf_biology"] == [file_path]
