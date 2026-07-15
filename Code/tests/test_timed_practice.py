"""Tests for timed practice save, grade, and reveal flow."""

from __future__ import annotations

from src.timed_practice import start_practice_attempt, submit_and_grade_attempt


def test_timed_practice_flow_hides_then_reveals_solution(temp_config) -> None:
    session, _practice, solution = start_practice_attempt("u", "german", "quiz", "German", "Essay", "adaptive", "easy", 1, "Q\n## Solutions\nA", temp_config)
    assert solution["visibility"] == "hidden_until_finished"
    result = submit_and_grade_attempt(session, "answer", 5, 10, [], [], [], temp_config)
    assert result["grade"] == 3.5
    assert result["solutions_visible"] is True
