"""Tests for chat history storage and RAG conversion."""

from __future__ import annotations

from src.chat_history_store import chat_messages_to_documents, new_chat_message, save_chat_media, save_chat_message


def test_chat_message_and_media_are_saved(temp_config) -> None:
    path = save_chat_media(b"image", "diagram.png", "user", "image", temp_config)
    assert path.exists()
    save_chat_message(new_chat_message(user_id="user", subject_key="chemistry", user_text="What is an ion?", image_ocr="Ion text"), temp_config)
    docs = chat_messages_to_documents("user", temp_config, "chemistry")
    assert docs and docs[0].metadata["user_id"] == "user"
    assert "Ion" in docs[0].text
