"""Dry-run timed quiz and exam flow without real Ollama."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.timed_practice import start_practice_attempt, submit_and_grade_attempt
from src.user_manager import create_user


def run_mode(mode: str, config, user_id: str) -> None:
    text = "Question 1: Explain DNA.\n\n## Solutions\nAnswer: DNA stores genetic information."
    session, _practice, solution = start_practice_attempt(user_id, "spf_biology", mode, "English", "DNA", "adaptive", "easy", 1, text, config)
    assert session.status == "running"
    assert solution["visibility"] == "hidden_until_finished"
    result = submit_and_grade_attempt(session, "DNA stores information", 8, 10, ["clear"], ["add detail"], ["practice diagrams"], config)
    assert result["solutions_visible"] is True
    assert result["grade"] == 5.0


def main() -> int:
    base = load_config(PROJECT_ROOT)
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        config = replace(base, data_dir=tmp_path / "data", user_data_root=tmp_path / "data" / "users", auth_db_file=tmp_path / "data" / "auth" / "users.json", vector_db_dir=tmp_path / "vector_db", subject_data_dir=tmp_path / "data" / "subjects")
        user = create_user("timer", "pw", config)
        run_mode("quiz", config, user["user_id"])
        run_mode("exam", config, user["user_id"])
    print("PASS: fake quiz generation, hidden solution, submission, grading, reveal")
    print("PASS: fake exam generation, hidden solution, submission, grading, reveal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
