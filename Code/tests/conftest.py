"""Shared pytest fixtures for beginner-readable tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import AppConfig
from src.subject_registry import setup_subject_folders


@pytest.fixture()
def temp_config(tmp_path: Path) -> AppConfig:
    """Create an isolated config so tests never touch private local files."""
    config = AppConfig(
        project_root=tmp_path,
        data_dir=tmp_path / "data",
        subject_data_dir=tmp_path / "data" / "subjects",
        vector_db_dir=tmp_path / "vector_db",
        feedback_file=tmp_path / "data" / "feedback" / "feedback.jsonl",
        stats_file=tmp_path / "data" / "stats" / "grades.csv",
        model_provider="ollama",
        ollama_host="http://localhost:11434",
        ollama_model="test-model",
        embedding_model="test-model",
        chunk_size=120,
        chunk_overlap=20,
    )
    setup_subject_folders(config)
    return config

