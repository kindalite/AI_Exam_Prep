"""Import-level coverage for the framework-neutral service package."""

from __future__ import annotations

import importlib


def test_all_service_modules_import_without_streamlit(monkeypatch) -> None:
    """Service modules must never depend on Streamlit."""
    real_import = __import__

    def guarded_import(name, *args, **kwargs):
        if name == "streamlit" or name.startswith("streamlit."):
            raise AssertionError("service import attempted to load Streamlit")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", guarded_import)
    modules = [
        "chat_service",
        "subject_service",
        "material_service",
        "quiz_service",
        "mock_exam_service",
        "grading_service",
        "study_plan_service",
        "feedback_service",
        "health_service",
        "identity_service",
        "retrieval_service",
        "upload_service",
        "structured_output",
    ]
    for module in modules:
        importlib.import_module(f"src.services.{module}")
