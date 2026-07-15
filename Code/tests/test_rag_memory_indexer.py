"""Tests for user-isolated RAG memory indexing."""

from __future__ import annotations

from src.chat_history_store import new_chat_message, save_chat_message
from src.rag_memory_indexer import index_user_memory_for_subject, retrieve_user_memory
from src.vector_store import InMemoryVectorStore


def test_rag_memory_index_filters_user_id(temp_config) -> None:
    save_chat_message(new_chat_message(user_id="a", subject_key="history", user_text="A secret"), temp_config)
    save_chat_message(new_chat_message(user_id="b", subject_key="history", user_text="B public"), temp_config)
    store = InMemoryVectorStore()
    result = index_user_memory_for_subject("b", "history", temp_config, vector_store=store)
    assert result["collection_name"] == "user_b__memory_history"
    chunks = retrieve_user_memory("b", "history", "public", temp_config, vector_store=store)
    assert chunks and all(chunk.metadata["user_id"] == "b" for chunk in chunks)
    assert "A secret" not in "\n".join(chunk.text for chunk in chunks)
