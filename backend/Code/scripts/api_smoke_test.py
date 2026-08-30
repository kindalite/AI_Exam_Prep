"""Fast in-process API smoke test with no live model or network dependency."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient

from src.api.dependencies import ApiServices, get_api_services, get_config
from src.api.main import create_app
from src.config import load_config
from src.subject_registry import setup_subject_folders


def main() -> int:
    """Check process health, catalogue, docs, and OpenAPI entirely in-process."""
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
        app = create_app()
        services = replace(
            ApiServices(),
            health=lambda cfg, started, api_version: {
                "status": "ok", "api_version": api_version, "uptime_seconds": 0,
                "vector_store": {"store_type": "in_memory", "reachable": True, "collection_count": 0, "collection_names": [], "message": "smoke"},
                "model_server_reachable": False, "model_provider": cfg.model_provider,
                "indexed_top_level_subjects": 0, "checked_at": "2026-08-19T00:00:00Z",
            },
        )
        app.dependency_overrides[get_config] = lambda: config
        app.dependency_overrides[get_api_services] = lambda: services
        with TestClient(app) as client:
            checks = {
                "health": client.get("/health").status_code,
                "subjects": client.get("/api/subjects").status_code,
                "docs": client.get("/docs").status_code,
                "openapi": client.get("/openapi.json").status_code,
            }
            assert len(client.get("/api/subjects").json()) == 15
        assert all(status == 200 for status in checks.values())
        print(checks)
    print("PASS: in-process API smoke completed without external services")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
