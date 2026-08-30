"""Exercise every Lovable-facing endpoint with fakes and print a concise report."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from datetime import date, timedelta
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from src.api.dependencies import ApiServices, get_api_services, get_config
from src.api.main import create_app
from src.config import load_config
from src.llm_client import LLMResponse
from src.services.chat_service import finalize_api_chat, prepare_api_chat, run_api_chat
from src.services.grading_service import generate_grading_api
from src.services.mock_exam_service import generate_mock_exam_api
from src.services.quiz_service import generate_quiz_api
from src.services.study_plan_service import generate_study_plan_api
from src.services.upload_service import import_student_document
from src.subject_registry import setup_subject_folders
from src.vector_store import InMemoryVectorStore


def fake_model(prompt, system_prompt, config):
    lowered = prompt.lower()
    if "backend schedules items" in lowered:
        value = {"summary": "Plan", "items": [{"title": "Review", "description": "Review", "duration_minutes": 30, "activity_type": "review"}]}
    elif "mock exam" in lowered:
        value = {"title": "Exam", "questions": [{"question_type": "short_answer", "prompt": "Explain", "points": 1, "options": [], "marking_criteria": ["Accurate"], "model_answer": "Hidden"}]}
    elif "grade this practice answer" in lowered:
        value = {"points_awarded": 1, "strengths": ["Relevant"], "missing_points": [], "improvement_advice": []}
    elif "exactly one json object" in lowered:
        value = {"title": "Quiz", "questions": [{"question_type": "short_answer", "prompt": "Explain", "options": [], "points": 1, "correct_index": None, "expected_answer": "Hidden", "explanation": "Hidden"}]}
    else:
        return LLMResponse("Grounded answer", True)
    return LLMResponse(json.dumps(value), True)


def main() -> int:
    """Run the complete backend contract with temporary storage."""
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        config = replace(load_config(PROJECT_ROOT), data_dir=root / "data", user_data_root=root / "data" / "users", subject_data_dir=root / "data" / "subjects", vector_db_dir=root / "vector_db")
        setup_subject_folders(config)
        store = InMemoryVectorStore()
        app = create_app()
        services = replace(
            ApiServices(),
            health=lambda cfg, started, api_version: {"status": "ok", "api_version": api_version, "uptime_seconds": 0, "vector_store": {"store_type": "in_memory", "reachable": True, "collection_count": 0, "collection_names": [], "message": "dry"}, "model_server_reachable": True, "model_provider": cfg.model_provider, "indexed_top_level_subjects": 0, "checked_at": "2026-08-19T00:00:00Z"},
            model_status=lambda cfg: {"provider": cfg.model_provider, "model": cfg.generation_model, "endpoint": "http://localhost:11434", "mode": "local", "reachable": True, "latency_ms": 1, "embedding_model": cfg.embedding_model, "fallback_provider": None, "message": "fake", "supports_streaming": True, "supports_vision": True},
            chat=partial(run_api_chat, vector_store=store, call_llm=fake_model),
            prepare_chat=partial(prepare_api_chat, vector_store=store),
            open_chat_stream=lambda prepared, config: iter(("Streamed ", "answer")),
            finalize_chat=finalize_api_chat,
            import_document=partial(import_student_document, vector_store=store),
            generate_quiz=partial(generate_quiz_api, vector_store=store, call_llm=fake_model),
            generate_mock_exam=partial(generate_mock_exam_api, vector_store=store, call_llm=fake_model),
            generate_study_plan=partial(generate_study_plan_api, vector_store=store, call_llm=fake_model),
            grade=partial(generate_grading_api, vector_store=store, call_llm=fake_model),
        )
        app.dependency_overrides[get_config] = lambda: config
        app.dependency_overrides[get_api_services] = lambda: services
        common = {"subject_id": "history", "component_subject_id": None, "language": "en", "academic_year": "2026/27", "grade_level": 11}
        chat = common | {"thread_id": "dry-thread", "question": "Explain", "learning_goal_id": None, "material_ids": [], "top_k": 4, "include_sources": True, "stream": False}
        requests = [
            ("GET", "/health", None), ("GET", "/api/model/status", None), ("GET", "/api/subjects", None), ("GET", "/api/subjects/history", None), ("GET", "/api/subjects/history/learning-goals", None), ("GET", "/api/subjects/history/materials", None),
            ("POST", "/api/chat", chat), ("POST", "/api/chat", chat | {"stream": True}),
            ("POST", "/api/quiz/generate", common | {"learning_goal_id": None, "topic": "sources", "difficulty": "easy", "question_count": 1, "material_ids": []}),
            ("POST", "/api/mock-exam/generate", common | {"total_points": 5, "difficulty": "medium", "topics": [], "learning_goal_ids": [], "material_ids": []}),
            ("POST", "/api/study-plan/generate", common | {"exam_date": (date.today() + timedelta(days=2)).isoformat(), "hours_per_week": 2, "weak_topics": [], "learning_goal_ids": [], "available_time_slots": [{"date": date.today().isoformat(), "start_time": "18:00", "end_time": "19:00"}], "max_daily_minutes": 60, "material_ids": []}),
            ("POST", "/api/grade", common | {"question": "Explain", "student_answer": "Answer", "max_points": 2, "marking_scheme": "Relevant", "material_ids": []}),
            ("POST", "/api/feedback", {"category": "other", "rating": 5, "message": None, "route": "/", "thread_id": None, "message_id": None, "subject_id": None, "language": None, "app_version": "dry"}),
        ]
        results = []
        headers = {"X-Student-Id": "dry-student"}
        with TestClient(app) as client:
            upload = client.post("/api/import/document", data={"subject_id": "history", "section": "notes", "language": "en"}, files={"file": ("notes.md", b"Source notes", "text/markdown")}, headers=headers)
            results.append(("POST /api/import/document", upload.status_code))
            for method, path, payload in requests:
                response = client.request(method, path, json=payload, headers=headers)
                results.append((f"{method} {path}", response.status_code))
        assert all(status == 200 for _name, status in results), results
        for name, status in results:
            print(f"PASS {status} {name}")
    print(f"PASS: {len(results)} Lovable contract calls completed without external services")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
