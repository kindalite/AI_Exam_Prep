"""Startup, middleware, CORS, health, and error tests for the FastAPI foundation."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.dependencies import ApiServices, get_api_services, get_config
from src.api.main import API_VERSION, create_app


def _client(temp_config) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_config] = lambda: temp_config
    app.dependency_overrides[get_api_services] = lambda: ApiServices(
        health=lambda config, started, api_version: {
            "status": "degraded",
            "api_version": api_version,
            "uptime_seconds": 0.01,
            "vector_store": {
                "store_type": "in_memory",
                "reachable": True,
                "collection_count": 0,
                "collection_names": [],
                "message": "test",
            },
            "model_server_reachable": False,
            "model_provider": config.model_provider,
            "indexed_top_level_subjects": 0,
            "checked_at": "2026-08-18T00:00:00+00:00",
        },
        model_status=lambda config: {
            "provider": config.model_provider,
            "model": config.ollama_model,
            "endpoint": "http://localhost:11434",
            "mode": "local",
            "reachable": False,
            "latency_ms": 0.01,
            "embedding_model": config.embedding_model,
            "fallback_provider": None,
            "message": "offline test",
        },
    )
    return TestClient(app)


def test_health_model_docs_and_openapi_start_without_live_model(temp_config) -> None:
    """The API must start and document itself without Ollama or network."""
    with _client(temp_config) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["api_version"] == API_VERSION
        assert health.json()["status"] == "degraded"
        assert health.headers["X-Request-Id"].startswith("req_")

        model = client.get("/api/model/status")
        assert model.status_code == 200
        assert model.json()["provider"] == "ollama"
        assert model.json()["reachable"] is False

        assert client.get("/docs").status_code == 200
        schema = client.get("/openapi.json")
        assert schema.status_code == 200
        assert schema.json()["info"]["version"] == API_VERSION


def test_request_id_is_validated_echoed_and_used_in_errors(temp_config) -> None:
    """Safe caller IDs are retained and invalid IDs are replaced."""
    with _client(temp_config) as client:
        accepted = client.get("/health", headers={"X-Request-Id": "frontend-123"})
        assert accepted.headers["X-Request-Id"] == "frontend-123"

        generated = client.get("/health", headers={"X-Request-Id": "bad id with spaces"})
        assert generated.headers["X-Request-Id"].startswith("req_")

        missing = client.get("/does-not-exist", headers={"X-Request-Id": "missing-1"})
        assert missing.status_code == 404
        assert missing.headers["X-Request-Id"] == "missing-1"
        assert missing.json() == {
            "error": {
                "code": "not_found",
                "message": "Not Found",
                "detail": "",
                "retryable": False,
                "request_id": "missing-1",
            }
        }


def test_cors_allows_only_local_frontend_contract(temp_config) -> None:
    """Preflight responses expose the configured local integration surface."""
    with _client(temp_config) as client:
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:8080",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-Student-Id,X-Request-Id,Content-Type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:8080"
        assert "GET" in response.headers["access-control-allow-methods"]
        assert "X-Student-Id" in response.headers["access-control-allow-headers"]

        actual = client.get("/health", headers={"Origin": "http://localhost:8080"})
        assert "X-Request-Id" in actual.headers["access-control-expose-headers"]


def test_openapi_uses_concrete_health_contract_refs(temp_config) -> None:
    """Available endpoints must expose named response models in OpenAPI."""
    with _client(temp_config) as client:
        schema = client.get("/openapi.json").json()
    health_ref = schema["paths"]["/health"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    model_ref = schema["paths"]["/api/model/status"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert health_ref.endswith("/BackendHealth")
    assert model_ref.endswith("/ModelStatus")
