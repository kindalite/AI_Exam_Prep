"""Feature test for per-user isolated RAG and practice memory."""

from __future__ import annotations

from src.chat_history_store import new_chat_message, save_chat_message
from src.rag_memory_indexer import index_user_memory_for_subject, retrieve_user_memory
from src.user_manager import create_user
from src.user_data_paths import get_user_root, get_user_subject_root
from src.vector_store import InMemoryVectorStore


def test_user_isolated_rag_and_practice_flow(temp_config) -> None:
    user_a = create_user("Template A", "pw", temp_config)
    note = get_user_subject_root(user_a["user_id"], "chemistry", temp_config) / "notes" / "chem.md"
    note.write_text("template chemistry", encoding="utf-8")
    private = get_user_root(user_a["user_id"], temp_config) / "reports" / "performance_reports.jsonl"
    private.parent.mkdir(parents=True, exist_ok=True)
    private.write_text("private report", encoding="utf-8")
    user_b = create_user("Student B", "pw", temp_config, template_user_id=user_a["user_id"])
    assert (get_user_subject_root(user_b["user_id"], "chemistry", temp_config) / "notes" / "chem.md").exists()
    assert not (get_user_root(user_b["user_id"], temp_config) / "reports" / "performance_reports.jsonl").exists()
    save_chat_message(new_chat_message(user_id=user_a["user_id"], subject_key="chemistry", user_text="A-only private"), temp_config)
    save_chat_message(new_chat_message(user_id=user_b["user_id"], subject_key="chemistry", user_text="B-only ions"), temp_config)
    store = InMemoryVectorStore()
    index_user_memory_for_subject(user_b["user_id"], "chemistry", temp_config, vector_store=store)
    results = retrieve_user_memory(user_b["user_id"], "chemistry", "ions", temp_config, vector_store=store)
    assert results
    combined = "\n".join(chunk.text for chunk in results)
    assert "B-only" in combined
    assert "A-only" not in combined
