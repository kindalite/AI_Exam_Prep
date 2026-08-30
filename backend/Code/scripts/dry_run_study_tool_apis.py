"""Offline HTTP dry run for all four structured AI study-tool endpoints."""

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
from src.services.grading_service import generate_grading_api
from src.services.mock_exam_service import generate_mock_exam_api
from src.services.quiz_service import generate_quiz_api
from src.services.study_plan_service import generate_study_plan_api
from src.subject_registry import setup_subject_folders
from src.vector_store import InMemoryVectorStore


def fake_model(prompt, system_prompt, config):
    """Return deterministic valid JSON for the requested operation."""
    lowered = prompt.lower()
    if "backend schedules items" in lowered:
        payload = {"summary": "Dry plan", "items": [{"title": "Review", "description": "Review notes", "duration_minutes": 30, "activity_type": "review"}]}
    elif "mock exam" in lowered:
        payload = {"title": "Dry exam", "questions": [{"question_type": "short_answer", "prompt": "Explain", "points": 2, "options": [], "marking_criteria": ["Accurate"], "model_answer": "Hidden"}]}
    elif "grade this practice answer" in lowered:
        payload = {"points_awarded": 1, "strengths": ["Relevant"], "missing_points": [], "improvement_advice": ["Add detail"]}
    else:
        payload = {"title": "Dry quiz", "questions": [{"question_type": "short_answer", "prompt": "Explain", "options": [], "points": 1, "correct_index": None, "expected_answer": "Hidden", "explanation": "Hidden"}]}
    return LLMResponse(json.dumps(payload), True)


def main() -> int:
    """Call all endpoints without Ollama, network, Chroma, or permanent writes."""
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        config = replace(
            load_config(PROJECT_ROOT),
            data_dir=root / "data",
            user_data_root=root / "data" / "users",
            subject_data_dir=root / "data" / "subjects",
            vector_db_dir=root / "vector_db",
        )
        setup_subject_folders(config)
        store = InMemoryVectorStore()
        app = create_app()
        app.dependency_overrides[get_config] = lambda: config
        app.dependency_overrides[get_api_services] = lambda: ApiServices(
            generate_quiz=partial(generate_quiz_api, vector_store=store, call_llm=fake_model),
            generate_mock_exam=partial(generate_mock_exam_api, vector_store=store, call_llm=fake_model),
            generate_study_plan=partial(generate_study_plan_api, vector_store=store, call_llm=fake_model),
            grade=partial(generate_grading_api, vector_store=store, call_llm=fake_model),
        )
        common = {"subject_id": "history", "component_subject_id": None, "language": "en", "academic_year": "2026/27", "grade_level": 11}
        requests = [
            ("/api/quiz/generate", common | {"learning_goal_id": None, "topic": "sources", "difficulty": "easy", "question_count": 1, "material_ids": []}),
            ("/api/mock-exam/generate", common | {"total_points": 10, "difficulty": "medium", "topics": [], "learning_goal_ids": [], "material_ids": []}),
            ("/api/study-plan/generate", common | {"exam_date": (date.today() + timedelta(days=2)).isoformat(), "hours_per_week": 2, "weak_topics": [], "learning_goal_ids": [], "available_time_slots": [{"date": date.today().isoformat(), "start_time": "18:00", "end_time": "19:00"}], "max_daily_minutes": 60, "material_ids": []}),
            ("/api/grade", common | {"question": "Explain", "student_answer": "Answer", "max_points": 2, "marking_scheme": "Relevant", "material_ids": []}),
        ]
        with TestClient(app) as client:
            results = []
            for path, payload in requests:
                response = client.post(path, json=payload, headers={"X-Student-Id": "dry-student"})
                response.raise_for_status()
                results.append((path, response.status_code))
        print(results)
    print("PASS: all four structured study-tool endpoints completed offline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
