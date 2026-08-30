"""Multipart contract tests for the user-scoped document import endpoint."""

from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient

from src.api.dependencies import ApiServices, get_api_services, get_config
from src.api.main import create_app
from src.services.upload_service import IndexBusyError, import_student_document
from src.vector_store import InMemoryVectorStore


def _client(temp_config, import_callable=None) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_config] = lambda: temp_config
    if import_callable:
        app.dependency_overrides[get_api_services] = lambda: ApiServices(
            import_document=import_callable
        )
    return TestClient(app)


def _request(client, *, headers=None, name="notes.md", content_type="text/markdown", data=None):
    fields = {
        "subject_id": "history",
        "section": "causes",
        "language": "en",
    }
    fields.update(data or {})
    return client.post(
        "/api/import/document",
        headers=headers or {},
        data=fields,
        files={"file": (name, b"# Notes\nA cause and consequence.", content_type)},
    )


def test_import_requires_identity_and_returns_api_shape(temp_config) -> None:
    """Successful multipart uploads expose computed fields and require identity."""
    store = InMemoryVectorStore()

    def isolated_import(**kwargs):
        return import_student_document(**kwargs, vector_store=store)

    with _client(temp_config, isolated_import) as client:
        missing = _request(client)
        success = _request(client, headers={"X-Student-Id": "student-a"})

    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == "student_identity_required"
    assert success.status_code == 200
    body = success.json()
    assert set(body) == {
        "material_id",
        "name",
        "type",
        "section",
        "language",
        "pages",
        "chunks_indexed",
        "status",
        "warnings",
        "added_at",
    }
    assert body["name"] == "notes.md" and body["status"] == "indexed"


def test_import_error_statuses_and_spf_component_rule(temp_config) -> None:
    """Upload failures map to stable status codes and error envelopes."""
    tiny = replace(temp_config, max_upload_bytes=3)
    with _client(tiny) as client:
        oversized = _request(client, headers={"X-Student-Id": "student-a"})
    with _client(temp_config) as client:
        unsupported = _request(
            client,
            headers={"X-Student-Id": "student-a"},
            name="payload.exe",
            content_type="application/octet-stream",
        )
        missing_component = _request(
            client,
            headers={"X-Student-Id": "student-a"},
            data={"subject_id": "spf_biology_chemistry", "language": "de"},
        )

    assert oversized.status_code == 413 and oversized.json()["error"]["code"] == "file_too_large"
    assert unsupported.status_code == 415 and unsupported.json()["error"]["code"] == "unsupported_media_type"
    assert missing_component.status_code == 422


def test_import_busy_maps_to_conflict(temp_config) -> None:
    """Concurrent full rebuilds return a retryable 409."""
    def busy(**kwargs):
        raise IndexBusyError("busy")

    with _client(temp_config, busy) as client:
        response = _request(client, headers={"X-Student-Id": "student-a"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "index_busy"
    assert response.json()["error"]["retryable"] is True

