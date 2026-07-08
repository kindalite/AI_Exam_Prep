"""Configuration loading for the local-first study assistant."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - depends on optional package installs
    load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AppConfig:
    """Typed settings used by the app and tests."""

    project_root: Path
    data_dir: Path
    subject_data_dir: Path
    vector_db_dir: Path
    feedback_file: Path
    stats_file: Path
    model_provider: str
    ollama_host: str
    ollama_model: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int


def load_config(project_root: Path | None = None) -> AppConfig:
    """Load environment variables and return an application configuration."""
    root = project_root or PROJECT_ROOT
    if load_dotenv is not None:
        load_dotenv(root / ".env")

    data_dir = root / "data"
    vector_db_dir = Path(os.getenv("CHROMA_DB_DIR", str(root / "vector_db")))
    if not vector_db_dir.is_absolute():
        vector_db_dir = root / vector_db_dir

    return AppConfig(
        project_root=root,
        data_dir=data_dir,
        subject_data_dir=data_dir / "subjects",
        vector_db_dir=vector_db_dir,
        feedback_file=data_dir / "feedback" / "feedback.jsonl",
        stats_file=data_dir / "stats" / "grades.csv",
        model_provider=os.getenv("MODEL_PROVIDER", "ollama"),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "deepseek-distilled-local"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "900")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "150")),
    )

