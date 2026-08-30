"""Lovable endpoint inventory and OpenAPI wire-contract assertions."""

from __future__ import annotations

import re
import json
from pathlib import Path

from src.api.main import create_app


EXPECTED_OPERATIONS = {
    ("/health", "get"),
    ("/api/model/status", "get"),
    ("/api/subjects", "get"),
    ("/api/subjects/{subject_id}", "get"),
    ("/api/subjects/{subject_id}/learning-goals", "get"),
    ("/api/subjects/{subject_id}/materials", "get"),
    ("/api/import/document", "post"),
    ("/api/chat", "post"),
    ("/api/quiz/generate", "post"),
    ("/api/mock-exam/generate", "post"),
    ("/api/study-plan/generate", "post"),
    ("/api/grade", "post"),
    ("/api/feedback", "post"),
}


def test_every_documented_method_path_and_named_response_contract_exists() -> None:
    """The OpenAPI surface contains every Lovable handoff operation."""
    schema = create_app().openapi()
    actual = {
        (path, method)
        for path, path_item in schema["paths"].items()
        for method in path_item
        if method in {"get", "post", "put", "patch", "delete"}
    }
    assert EXPECTED_OPERATIONS <= actual
    for path, method in EXPECTED_OPERATIONS:
        operation = schema["paths"][path][method]
        assert operation["responses"]
        assert operation.get("operationId")


def test_schema_properties_are_snake_case_and_chat_documents_both_modes() -> None:
    """Core wire fields stay snake_case and chat exposes JSON plus SSE."""
    schema = create_app().openapi()
    snake_case = re.compile(r"^[a-z][a-z0-9_]*$")
    for definition in schema["components"]["schemas"].values():
        for field_name in definition.get("properties", {}):
            assert snake_case.fullmatch(field_name), field_name
    chat_content = schema["paths"]["/api/chat"]["post"]["responses"]["200"]["content"]
    assert "application/json" in chat_content
    assert "text/event-stream" in chat_content


def test_core_response_refs_are_concrete() -> None:
    """Lovable-facing operations use named response objects, not arbitrary blobs."""
    schema = create_app().openapi()
    expected_refs = {
        "/health": "BackendHealth",
        "/api/model/status": "ModelStatus",
        "/api/chat": "ChatResponse",
        "/api/quiz/generate": "Quiz",
        "/api/mock-exam/generate": "MockExam",
        "/api/study-plan/generate": "StudyPlan",
        "/api/grade": "GradingResult",
        "/api/feedback": "FeedbackResponse",
    }
    for path, model in expected_refs.items():
        method = "get" if path in {"/health", "/api/model/status"} else "post"
        response_schema = schema["paths"][path][method]["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema["$ref"].endswith(f"/{model}")


def test_committed_openapi_matches_real_app() -> None:
    """The frontend handoff spec is generated from the current application."""
    exported = json.loads(
        (Path(__file__).resolve().parents[2] / "docs" / "openapi.json").read_text(
            encoding="utf-8"
        )
    )
    assert exported == create_app().openapi()
