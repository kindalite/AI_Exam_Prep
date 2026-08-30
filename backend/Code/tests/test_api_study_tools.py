"""Structured AI study-tool API tests with fake models and isolated storage."""

from __future__ import annotations

import json
from datetime import date, timedelta
from functools import partial

from fastapi.testclient import TestClient

from src.api.dependencies import ApiServices, get_api_services, get_config
from src.api.main import create_app
from src.chunking import TextChunk
from src.llm_client import LLMResponse
from src.services.grading_service import generate_grading_api
from src.services.mock_exam_service import generate_mock_exam_api
from src.services.quiz_service import generate_quiz_api
from src.services.study_plan_service import generate_study_plan_api
from src.user_data_paths import get_user_root, user_subject_collection_name
from src.vector_store import InMemoryVectorStore


QUIZ_JSON = json.dumps(
    {
        "title": "Source Quiz",
        "questions": [
            {
                "question_type": "multiple_choice",
                "prompt": "Choose the supported claim.",
                "options": ["A", "B"],
                "points": 1,
                "correct_index": 1,
                "expected_answer": "B",
                "explanation": "The source supports B.",
            },
            {
                "question_type": "short_answer",
                "prompt": "Explain briefly.",
                "options": [],
                "points": 2,
                "correct_index": None,
                "expected_answer": "A grounded explanation.",
                "explanation": "Use the evidence.",
            },
        ],
    }
)

EXAM_JSON = json.dumps(
    {
        "title": "Mock Exam",
        "questions": [
            {
                "question_type": "short_answer",
                "prompt": "Define the concept.",
                "points": 2,
                "options": [],
                "marking_criteria": ["Correct definition"],
                "model_answer": "Protected definition",
            },
            {
                "question_type": "long_answer",
                "prompt": "Evaluate the evidence.",
                "points": 3,
                "options": [],
                "marking_criteria": ["Evidence", "Reasoning"],
                "model_answer": "Protected essay",
            },
        ],
    }
)

PLAN_JSON = json.dumps(
    {
        "summary": "Two focused sessions before the exam.",
        "items": [
            {
                "title": "Review",
                "description": "Review source notes.",
                "duration_minutes": 30,
                "activity_type": "review",
            },
            {
                "title": "Practice",
                "description": "Answer one practice task.",
                "duration_minutes": 45,
                "activity_type": "practice",
            },
        ],
    }
)

GRADE_JSON = json.dumps(
    {
        "points_awarded": 1,
        "strengths": ["Uses evidence"],
        "missing_points": ["Needs a date"],
        "improvement_advice": ["Add the event date"],
        "rubric_used": ["Invented rubric must be ignored"],
    }
)


def _model(prompt, system_prompt, config):
    if "backend schedules items" in prompt.lower():
        return LLMResponse(PLAN_JSON, True)
    if "mock exam" in prompt.lower():
        return LLMResponse(EXAM_JSON, True)
    if "grade this practice answer" in prompt.lower():
        return LLMResponse(GRADE_JSON, True)
    return LLMResponse(QUIZ_JSON, True)


def _client(temp_config, store, model=_model):
    app = create_app()
    app.dependency_overrides[get_config] = lambda: temp_config
    app.dependency_overrides[get_api_services] = lambda: ApiServices(
        generate_quiz=partial(generate_quiz_api, vector_store=store, call_llm=model),
        generate_mock_exam=partial(generate_mock_exam_api, vector_store=store, call_llm=model),
        generate_study_plan=partial(generate_study_plan_api, vector_store=store, call_llm=model),
        grade=partial(generate_grading_api, vector_store=store, call_llm=model),
    )
    return TestClient(app)


def _academic(subject="history", language="en") -> dict:
    return {
        "subject_id": subject,
        "component_subject_id": None,
        "language": language,
        "academic_year": "2026/27",
        "grade_level": 11,
    }


def test_quiz_hides_solutions_repairs_once_and_persists_per_student(temp_config) -> None:
    """Quiz output is repaired once, visible questions hide answers, and storage is isolated."""
    calls: list[str] = []

    def repair_model(prompt, system_prompt, config):
        calls.append(prompt)
        return LLMResponse("not json" if len(calls) == 1 else QUIZ_JSON, True)

    with _client(temp_config, InMemoryVectorStore(), repair_model) as client:
        response = client.post(
            "/api/quiz/generate",
            json=_academic() | {
                "learning_goal_id": None,
                "topic": "causes",
                "difficulty": "adaptive",
                "question_count": 2,
                "material_ids": ["missing-material"],
            },
            headers={"X-Student-Id": "student-a"},
        )
    assert response.status_code == 200, body
    body = response.json()
    assert len(calls) == 2 and body["difficulty"] == "medium"
    assert all(question["correct_index"] is None for question in body["questions"])
    assert all(question["expected_answer"] is None for question in body["questions"])
    root_a = get_user_root("student-a", temp_config)
    root_b = get_user_root("student-b", temp_config)
    solution = json.loads(next((root_a / "generated_practice" / "solution_sets").glob("*.json")).read_text())
    assert "The source supports B." in solution["solution_set"]
    assert not root_b.exists()


def test_mock_exam_normalizes_points_hides_answers_and_spf_combines(temp_config) -> None:
    """Combined SPF evidence is used and point totals are exact without answer leakage."""
    store = InMemoryVectorStore()
    for key, text in (("spf_biology", "cell evidence"), ("spf_chemistry", "ion evidence")):
        store.rebuild_collection(
            user_subject_collection_name("student-a", key),
            [TextChunk(text, {"chunk_id": key, "source_name": f"{key}.md", "user_id": "student-a", "material_id": f"mat_{key}"})],
        )
    captured: list[str] = []

    def model(prompt, system_prompt, config):
        captured.append(prompt)
        return LLMResponse(EXAM_JSON, True)

    with _client(temp_config, store, model) as client:
        response = client.post(
            "/api/mock-exam/generate",
            json=_academic("spf_biology_chemistry", "de") | {
                "total_points": 10,
                "difficulty": "hard",
                "topics": ["cells", "ions"],
                "learning_goal_ids": [],
                "material_ids": [],
            },
            headers={"X-Student-Id": "student-a"},
        )
    body = response.json()
    assert response.status_code == 200
    assert sum(question["points"] for question in body["questions"]) == 10
    assert all(question["model_answer"] is None for question in body["questions"])
    assert "cell evidence" in captured[0] and "ion evidence" in captured[0]


def test_study_plan_uses_slots_without_overlap_and_does_not_write_planner(temp_config) -> None:
    """Plan proposals respect slots/daily caps and never become frontend planner CRUD."""
    exam_date = date.today() + timedelta(days=3)
    with _client(temp_config, InMemoryVectorStore()) as client:
        response = client.post(
            "/api/study-plan/generate",
            json=_academic("french", "fr") | {
                "exam_date": exam_date.isoformat(),
                "hours_per_week": 3,
                "weak_topics": ["vocabulary"],
                "learning_goal_ids": [],
                "available_time_slots": [
                    {"date": date.today().isoformat(), "start_time": "18:00", "end_time": "20:00"}
                ],
                "max_daily_minutes": 90,
                "material_ids": [],
            },
            headers={"X-Student-Id": "student-a"},
        )
    body = response.json()
    assert response.status_code == 200, body
    first, second = body["items"]
    assert first["end_time"] <= second["start_time"]
    assert sum(item["duration_minutes"] for item in body["items"]) <= 90
    assert not (get_user_root("student-a", temp_config) / "planner").exists()


def test_grade_exact_math_grounded_rubric_and_report_isolation(temp_config) -> None:
    """Grading uses the exact formula and only request/file rubric lines."""
    with _client(temp_config, InMemoryVectorStore()) as client:
        response = client.post(
            "/api/grade",
            json=_academic("biology", "de") | {
                "question": "Explain ATP.",
                "student_answer": "ATP stores energy.",
                "max_points": 3,
                "marking_scheme": "- Mentions energy transfer",
                "material_ids": [],
            },
            headers={"X-Student-Id": "student-b"},
        )
    body = response.json()
    assert response.status_code == 200
    assert body["swiss_grade"] == 1 + 5 / 3
    assert body["rubric_used"] == ["Mentions energy transfer"]
    report = get_user_root("student-b", temp_config) / "reports" / "performance_reports.jsonl"
    assert report.exists()
    assert not (get_user_root("student-a", temp_config) / "reports" / "performance_reports.jsonl").exists()


def test_malformed_twice_returns_structured_error(temp_config) -> None:
    """Two malformed outputs fail instead of leaking a free-form response."""
    bad_model = lambda *args, **kwargs: LLMResponse("still not json", True)
    with _client(temp_config, InMemoryVectorStore(), bad_model) as client:
        response = client.post(
            "/api/quiz/generate",
            json=_academic() | {
                "learning_goal_id": None,
                "topic": None,
                "difficulty": "easy",
                "question_count": 2,
                "material_ids": [],
            },
            headers={"X-Student-Id": "student-a"},
        )
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "invalid_model_output"
