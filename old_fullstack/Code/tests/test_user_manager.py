"""Tests for local user creation and template copying."""

from __future__ import annotations

from src.user_manager import authenticate_user, create_user
from src.user_data_paths import get_user_root, get_user_subject_root


def test_create_user_and_copy_only_study_material(temp_config) -> None:
    a = create_user("Alice", "pw", temp_config)
    notes = get_user_subject_root(a["user_id"], "german", temp_config) / "notes" / "grammar.md"
    notes.write_text("grammar", encoding="utf-8")
    private = get_user_root(a["user_id"], temp_config) / "chat_history" / "messages.jsonl"
    private.parent.mkdir(parents=True, exist_ok=True)
    private.write_text("private", encoding="utf-8")
    b = create_user("Bob", "pw", temp_config, template_user_id=a["user_id"])
    assert authenticate_user("Bob", "pw", temp_config)
    assert (get_user_subject_root(b["user_id"], "german", temp_config) / "notes" / "grammar.md").exists()
    assert not (get_user_root(b["user_id"], temp_config) / "chat_history" / "messages.jsonl").exists()
