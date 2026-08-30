"""Tests for local feedback storage."""

from __future__ import annotations

from src.feedback import read_feedback, save_feedback


def test_feedback_saves_and_reads_jsonl(temp_config) -> None:
    """Feedback should be saved locally so prompts and material can improve later."""
    record = save_feedback("biology", "chat", "question", "answer", 5, "useful", ["chunk-1"], config=temp_config)
    records = read_feedback(temp_config.feedback_file)
    assert records[0]["timestamp"]
    assert records[0]["subject"] == "biology"
    assert records[0]["feature"] == "chat"
    assert records[0]["rating"] == 5
    assert record["comment"] == "useful"

