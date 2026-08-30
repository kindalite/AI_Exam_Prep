"""Tests for persistent timed attempt sessions."""

from __future__ import annotations

from dataclasses import replace

from src.attempt_session import create_timed_session, load_timed_session, mark_session_status, refresh_expired_session, solution_is_visible


def test_timed_session_persists_and_solution_visibility(temp_config) -> None:
    session = create_timed_session("u", "german", "quiz", 1, "q.json", "s.json", temp_config)
    loaded = load_timed_session("u", session.attempt_id, temp_config)
    assert loaded and loaded.status == "running"
    assert not solution_is_visible(loaded, temp_config)
    graded = mark_session_status(loaded, "graded", temp_config)
    assert solution_is_visible(graded, temp_config)


def test_expired_session_auto_submits(temp_config) -> None:
    config = replace(temp_config, allow_auto_submit_on_timer_end=True)
    session = create_timed_session("u", "german", "quiz", 0, "q.json", "s.json", config)
    assert refresh_expired_session(session, config).status == "submitted"
