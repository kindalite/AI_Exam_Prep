"""Tests for local performance JSONL storage."""

from __future__ import annotations

from src.performance_tracker import new_attempt, read_practice_attempts, save_practice_attempt, summarize_performance


def test_performance_tracker_saves_reads_and_summarizes(temp_config) -> None:
    attempt = new_attempt(subject_key="german", topic="Essay", points_achieved=8, maximum_points=10, grade=5.0)
    save_practice_attempt(attempt, temp_config)
    rows = read_practice_attempts(temp_config, "german")
    assert rows[0]["topic"] == "Essay"
    assert summarize_performance("german", temp_config)["average_grade"] == 5.0
