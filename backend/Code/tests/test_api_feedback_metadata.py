"""Feedback isolation and non-authoritative AI provenance tests."""

from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient

from src.ai_metadata_store import (
    AIProvenanceRecord,
    ai_metadata_path,
    find_ai_provenance,
    read_ai_provenance,
    save_ai_provenance,
)
from src.api.dependencies import ApiServices, get_api_services, get_config
from src.api.main import create_app
from src.feedback import api_feedback_path, read_feedback


def _payload(**updates) -> dict:
    payload = {
        "category": "answer_quality",
        "rating": 4,
        "message": "The citation was useful.",
        "route": "/subjects/history/chat",
        "thread_id": "thread-1",
        "message_id": "ai-1",
        "subject_id": "history",
        "language": "en",
        "app_version": "1.0.0",
    }
    payload.update(updates)
    return payload


def _client(temp_config, services=None):
    app = create_app()
    app.dependency_overrides[get_config] = lambda: temp_config
    if services is not None:
        app.dependency_overrides[get_api_services] = lambda: services
    return TestClient(app)


def test_feedback_validation_two_user_isolation_and_malformed_tolerance(temp_config) -> None:
    """Feedback is validated, append-only per student, and ignores corrupt lines."""
    path_a = api_feedback_path("student-a", temp_config)
    path_a.parent.mkdir(parents=True, exist_ok=True)
    path_a.write_text("{malformed\n", encoding="utf-8")
    with _client(temp_config) as client:
        first = client.post("/api/feedback", json=_payload(), headers={"X-Student-Id": "student-a"})
        second = client.post(
            "/api/feedback",
            json=_payload(rating=None, message="Bug details", category="bug"),
            headers={"X-Student-Id": "student-b"},
        )
        invalid = client.post(
            "/api/feedback",
            json=_payload(rating=None, message=None),
            headers={"X-Student-Id": "student-a"},
        )
    assert first.status_code == second.status_code == 200
    assert set(first.json()) == {"feedback_id", "created_at"}
    assert invalid.status_code == 422
    rows_a = read_feedback(path_a)
    rows_b = read_feedback(api_feedback_path("student-b", temp_config))
    assert len(rows_a) == len(rows_b) == 1
    assert rows_a[0]["student_id"] == "student-a"
    assert rows_b[0]["student_id"] == "student-b"
    assert "user_task" not in rows_a[0] and "app_answer" not in rows_a[0]


def test_feedback_storage_failure_uses_common_error_envelope(temp_config) -> None:
    """Filesystem failures are safe, structured, and contain no private payload echo."""
    def broken(**kwargs):
        raise OSError("private answer must not be returned")

    services = replace(ApiServices(), feedback=broken)
    with _client(temp_config, services) as client:
        response = client.post(
            "/api/feedback", json=_payload(message="private feedback"), headers={"X-Student-Id": "student-a"}
        )
    body = response.json()
    assert response.status_code == 503
    assert body["error"]["code"] == "feedback_storage_failed"
    assert "private" not in body["error"]["detail"]


def test_ai_metadata_lookup_is_isolated_minimal_and_malformed_tolerant(temp_config) -> None:
    """Provenance keys are student-specific and never contain prompt/answer text."""
    record = AIProvenanceRecord(
        student_id="student-a",
        thread_id="thread-1",
        python_message_id="ai-1",
        source_ids=("chunk-1",),
        material_ids=("mat-1",),
        used_model="fake",
        provider="ollama",
        retrieval_summary={"chunks_used": 1},
        subject_id="history",
        component_subject_id=None,
        language="en",
        generated_at="2026-08-19T10:00:00Z",
    )
    save_ai_provenance(record, temp_config)
    path = ai_metadata_path("student-a", temp_config)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("not-json\n")
    found = find_ai_provenance("student-a", "thread-1", "ai-1", temp_config)
    assert found is not None and found["store_role"] == "non_authoritative_ai_provenance"
    assert find_ai_provenance("student-b", "thread-1", "ai-1", temp_config) is None
    assert len(read_ai_provenance("student-a", temp_config)) == 1
    assert not ({"prompt", "question", "answer", "assistant_answer"} & set(found))
