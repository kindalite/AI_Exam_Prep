"""Offline Stage-1 chat API dry run with isolated in-memory evidence."""

from __future__ import annotations

import sys
from dataclasses import replace
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from src.api.dependencies import ApiServices, get_api_services, get_config
from src.api.main import create_app
from src.chunking import TextChunk
from src.config import load_config
from src.llm_client import LLMResponse
from src.services.chat_service import run_api_chat
from src.user_data_paths import user_subject_collection_name
from src.vector_store import InMemoryVectorStore


def main() -> None:
    """Exercise the full HTTP adapter without network or Ollama."""
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        config = replace(
            load_config(PROJECT_ROOT),
            data_dir=root / "data",
            user_data_root=root / "data" / "users",
            subject_data_dir=root / "data" / "subjects",
            vector_db_dir=root / "vector_db",
        )
        store = InMemoryVectorStore()
        store.rebuild_collection(
            user_subject_collection_name("dry-run-student", "history"),
            [
                TextChunk(
                    "The dry-run primary source was written during the event.",
                    {
                        "chunk_id": "dry-history-1",
                        "source_name": "primary-source.md",
                        "material_id": "mat_dry_history",
                        "source_layer": "user_material",
                        "user_id": "dry-run-student",
                    },
                )
            ],
        )
        app = create_app()
        app.dependency_overrides[get_config] = lambda: config
        app.dependency_overrides[get_api_services] = lambda: ApiServices(
            chat=partial(
                run_api_chat,
                vector_store=store,
                call_llm=lambda *args, **kwargs: LLMResponse("A grounded dry-run answer.", True),
            )
        )
        payload = {
            "thread_id": "dry-thread",
            "subject_id": "history",
            "component_subject_id": None,
            "language": "en",
            "academic_year": "2026/27",
            "grade_level": 11,
            "question": "Why is this a primary source?",
            "learning_goal_id": None,
            "material_ids": ["mat_dry_history"],
            "top_k": 4,
            "include_sources": True,
            "stream": False,
        }
        with TestClient(app) as client:
            response = client.post(
                "/api/chat", json=payload, headers={"X-Student-Id": "dry-run-student"}
            )
        response.raise_for_status()
        body = response.json()
        assert body["answer"] == "A grounded dry-run answer."
        assert body["sources"][0]["material_id"] == "mat_dry_history"
        print(body)
    print("PASS: non-streaming chat stayed student-scoped and did not require Ollama")


if __name__ == "__main__":
    main()
