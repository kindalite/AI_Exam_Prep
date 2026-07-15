"""Verify the local conda/Python environment for Alim Study Assistant."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config

REQUIRED = ["streamlit", "requests", "pandas", "chromadb", "sentence_transformers", "ollama", "pypdf", "docx", "pytest"]
OPTIONAL = ["fitz", "PIL", "pytesseract", "bs4", "trafilatura", "ddgs", "faster_whisper", "soundfile"]


def line(status: str, message: str) -> None:
    print(f"{status}: {message}")


def can_import(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


def main() -> int:
    config = load_config(PROJECT_ROOT)
    failures = 0
    version = sys.version_info
    if version.major == 3 and version.minor == 11:
        line("PASS", f"Python {sys.version.split()[0]}")
    else:
        line("FAIL", f"Python 3.11 expected, found {sys.version.split()[0]}")
        failures += 1
    expected = os.path.expanduser(config.expected_conda_env_path)
    if "alim_study_assistant" in sys.executable or sys.executable.startswith(expected):
        line("PASS", f"Executable is in target env: {sys.executable}")
    else:
        line("WARN", f"Executable is not the target env {expected}: {sys.executable}")
    for package in REQUIRED:
        if can_import(package):
            line("PASS", f"required package imports: {package}")
        else:
            line("FAIL", f"missing required package: {package}")
            failures += 1
    for package in OPTIONAL:
        line("PASS" if can_import(package) else "WARN", f"optional package {'imports' if can_import(package) else 'not installed'}: {package}")
    env_example = PROJECT_ROOT / ".env.example"
    if env_example.exists() and "OLLAMA_MODEL=gemma3:4b" in env_example.read_text(encoding="utf-8"):
        line("PASS", ".env.example configures OLLAMA_MODEL=gemma3:4b")
    else:
        line("FAIL", ".env.example must contain OLLAMA_MODEL=gemma3:4b")
        failures += 1
    try:
        import app  # noqa: F401
        line("PASS", "app imports")
    except Exception as exc:
        line("FAIL", f"app import failed: {exc}")
        failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
