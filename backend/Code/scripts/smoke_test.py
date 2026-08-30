"""Smoke test for quickly checking that the app basics still work."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def pass_message(message: str) -> None:
    """Print a readable PASS line."""
    print(f"PASS: {message}")


def main() -> int:
    """Run a small set of checks without calling Ollama."""
    modules = [
        "app",
        "src.config",
        "src.subject_registry",
        "src.chunking",
        "src.prompts",
        "src.grader",
    ]
    for module_name in modules:
        importlib.import_module(module_name)
        pass_message(f"imported {module_name}")

    from src.chunking import chunk_text
    from src.grader import calculate_grade
    from src.prompts import build_chat_prompt
    from src.subject_registry import build_subject_registry

    subject = build_subject_registry()["spf_biology"]
    chunks = chunk_text("Cells contain DNA and proteins.", {"source_name": "sample.md", "subject": "biology"})
    assert chunks
    pass_message("created sample chunk")

    prompt = build_chat_prompt(subject, "German", "Was ist DNA?", "DNA context", "Goal", "Criteria")
    assert "Biology" in prompt
    pass_message("built chat prompt")

    assert calculate_grade(5, 10).grade == 3.5
    pass_message("calculated grading formula")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
