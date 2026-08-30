"""Smoke import tests for the app entry point."""

from __future__ import annotations

import importlib


def test_app_imports_without_streamlit_runtime() -> None:
    """Importing app.py should not launch Streamlit or call Ollama."""
    app = importlib.import_module("app")
    assert hasattr(app, "main")

