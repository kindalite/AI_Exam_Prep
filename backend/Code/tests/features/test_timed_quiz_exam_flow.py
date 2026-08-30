"""Feature test for timed quiz and exam flow."""

from __future__ import annotations

from src.timed_practice import start_practice_attempt, submit_and_grade_attempt
from src.user_manager import create_user


def _run(mode: str, temp_config, user_id: str) -> None:
    session, practice, solution = start_practice_attempt(user_id, "german", mode, "German", "Essay", "adaptive", "easy", 1, "Q1\n## Solutions\nA1", temp_config)
    assert practice["question_set"] == "Q1"
    assert solution["visibility"] == "hidden_until_finished"
    result = submit_and_grade_attempt(session, "A1", 9, 10, ["good"], ["minor"], ["next"], temp_config)
    assert result["solutions_visible"] is True
    assert result["report"]["grade"] == 5.5
    assert result["indexed"]["user_id"] == user_id


def test_timed_quiz_exam_flow(temp_config) -> None:
    user = create_user("Timed", "pw", temp_config)
    _run("quiz", temp_config, user["user_id"])
    _run("exam", temp_config, user["user_id"])
