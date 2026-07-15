"""Tests for environment metadata and verifier script."""

from __future__ import annotations

from pathlib import Path


def test_environment_and_requirements_are_consistent() -> None:
    root = Path(__file__).resolve().parents[1]
    env = (root / "environment.yml").read_text(encoding="utf-8")
    reqs = [line.strip() for line in (root / "requirements.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert "name: alim_study_assistant" in env
    for requirement in ["streamlit==1.59.0", "ollama==0.6.2", "pytest==9.1.1"]:
        assert requirement in reqs
        assert requirement in env


def test_verify_environment_script_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "scripts" / "verify_environment.py").exists()
