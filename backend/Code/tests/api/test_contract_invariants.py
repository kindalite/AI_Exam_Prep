"""Cross-endpoint Lovable invariants not tied to one service implementation."""

from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient

from src.api.dependencies import get_config
from src.api.main import create_app


def test_validation_errors_request_ids_cors_subject_count_and_spf_nesting(temp_config) -> None:
    """Shared validation, request correlation, CORS, and catalogue invariants hold."""
    app = create_app()
    app.dependency_overrides[get_config] = lambda: temp_config
    with TestClient(app) as client:
        invalid = client.post(
            "/api/feedback",
            json={"category": "bug", "rating": None, "message": None},
            headers={"X-Student-Id": "student-a", "X-Request-Id": "contract-1"},
        )
        subjects = client.get("/api/subjects")
        cors = client.options(
            "/api/chat",
            headers={
                "Origin": "http://localhost:8080",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-Student-Id,X-Request-Id,Content-Type",
            },
        )
    assert invalid.status_code == 422
    assert invalid.headers["X-Request-Id"] == "contract-1"
    assert set(invalid.json()) == {"error"}
    assert set(invalid.json()["error"]) == {"code", "message", "detail", "retryable", "request_id"}
    assert len(subjects.json()) == 15
    assert not ({"spf_biology", "spf_chemistry"} & {item["subject_id"] for item in subjects.json()})
    spf = next(item for item in subjects.json() if item["subject_id"] == "spf_biology_chemistry")
    assert {item["subject_id"] for item in spf["components"]} == {"spf_biology", "spf_chemistry"}
    assert cors.headers["access-control-allow-origin"] == "http://localhost:8080"


def test_feedback_timestamp_is_iso_utc(temp_config) -> None:
    """A representative API persistence timestamp parses as timezone-aware UTC."""
    app = create_app()
    app.dependency_overrides[get_config] = lambda: temp_config
    with TestClient(app) as client:
        response = client.post(
            "/api/feedback",
            json={"category": "other", "rating": 5, "message": None},
            headers={"X-Student-Id": "student-a"},
        )
    timestamp = response.json()["created_at"]
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    assert parsed.utcoffset() is not None
