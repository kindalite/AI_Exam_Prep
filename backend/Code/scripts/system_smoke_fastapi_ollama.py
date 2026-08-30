"""Explicitly opt-in real Ollama smoke through the FastAPI chat endpoint."""

from __future__ import annotations

import os
import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from src.api.dependencies import get_config
from src.api.main import create_app
from src.config import load_config
from src.subject_registry import setup_subject_folders


def main() -> int:
    if os.getenv("RUN_FASTAPI_OLLAMA_SMOKE") != "1":
        print("SKIP: set RUN_FASTAPI_OLLAMA_SMOKE=1 to call Ollama through FastAPI")
        return 0
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        config = replace(load_config(PROJECT_ROOT), model_provider="ollama", data_dir=root / "data", user_data_root=root / "data" / "users", subject_data_dir=root / "data" / "subjects", vector_db_dir=root / "vector_db")
        setup_subject_folders(config)
        app = create_app()
        app.dependency_overrides[get_config] = lambda: config
        payload = {"thread_id": "live-smoke", "subject_id": "history", "component_subject_id": None, "language": "en", "academic_year": "2026/27", "grade_level": 11, "question": "Reply in one sentence: why study history?", "learning_goal_id": None, "material_ids": [], "top_k": 2, "include_sources": False, "stream": False}
        with TestClient(app) as client:
            response = client.post("/api/chat", json=payload, headers={"X-Student-Id": "smoke-student"})
        if response.status_code != 200:
            print(f"FAIL: HTTP {response.status_code} {response.json().get('error', {}).get('code')}")
            return 1
        print(f"PASS: FastAPI/Ollama answered with {len(response.json()['answer'])} characters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
