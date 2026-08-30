"""Local per-user chat history and media storage for RAG memory."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .document_loaders import LoadedDocument
from .user_data_paths import get_user_root, relative_to_user, sanitize_username
from .utils import ensure_directory, utc_timestamp


@dataclass(frozen=True)
class ChatMessageRecord:
    """One chat interaction that can later become RAG memory."""

    message_id: str
    session_id: str
    user_id: str
    subject_key: str
    timestamp: str
    language: str
    user_text: str
    audio_transcript: str | None
    image_ocr: str | None
    image_description: str | None
    assistant_answer: str | None
    source_chunk_ids: list[str] = field(default_factory=list)
    source_layers: list[str] = field(default_factory=list)
    feature: str = "chat"
    source_layer: str = "chat_history"
    source_type: str = "chat_message"
    topic: str = ""
    learning_goal: str = ""
    visibility: str = "user_visible"


def new_chat_message(**kwargs) -> ChatMessageRecord:
    """Create a chat message with safe defaults."""
    data = {
        "message_id": uuid.uuid4().hex,
        "session_id": uuid.uuid4().hex,
        "user_id": "default",
        "subject_key": "general",
        "timestamp": utc_timestamp(),
        "language": "German",
        "user_text": "",
        "audio_transcript": None,
        "image_ocr": None,
        "image_description": None,
        "assistant_answer": None,
        "source_chunk_ids": [],
        "source_layers": [],
        "topic": "",
        "learning_goal": "",
    }
    data.update(kwargs)
    data["user_id"] = sanitize_username(data["user_id"])
    return ChatMessageRecord(**data)


def _messages_path(user_id: str, config) -> Path:
    """Return the user's chat messages JSONL path."""
    return get_user_root(user_id, config) / "chat_history" / "messages.jsonl"


def save_chat_message(record: ChatMessageRecord, config) -> dict:
    """Append one chat message to the user's isolated local log."""
    path = _messages_path(record.user_id, config)
    ensure_directory(path.parent)
    row = asdict(record)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def read_chat_messages(user_id: str, config, subject_key: str | None = None) -> list[dict]:
    """Read chat messages for one user, optionally filtered by subject."""
    path = _messages_path(user_id, config)
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if subject_key:
        rows = [row for row in rows if row.get("subject_key") == subject_key]
    return rows


def save_chat_media(file_bytes: bytes, original_name: str, user_id: str, modality: str, config) -> Path:
    """Save uploaded chat media under the current user's isolated folder."""
    safe_user = sanitize_username(user_id)
    safe_name = Path(original_name).name.replace("/", "_") or f"media_{uuid.uuid4().hex}"
    folder = "audio" if modality.startswith("audio") else "images"
    target = get_user_root(safe_user, config) / "chat_media" / folder / f"{uuid.uuid4().hex}_{safe_name}"
    ensure_directory(target.parent)
    target.write_bytes(file_bytes)
    return target


def chat_messages_to_documents(user_id: str, config, subject_key: str | None = None) -> list[LoadedDocument]:
    """Convert stored chat messages into LoadedDocument records for RAG."""
    documents: list[LoadedDocument] = []
    for row in read_chat_messages(user_id, config, subject_key):
        parts = [
            f"Student: {row.get('user_text', '')}",
            f"Audio transcript: {row.get('audio_transcript') or ''}",
            f"Image OCR: {row.get('image_ocr') or ''}",
            f"Image description: {row.get('image_description') or ''}",
            f"Assistant: {row.get('assistant_answer') or ''}",
        ]
        text = "\n".join(part for part in parts if part.split(": ", 1)[-1].strip())
        metadata = {
            "user_id": sanitize_username(user_id),
            "session_id": row.get("session_id", ""),
            "subject": row.get("subject_key", "general"),
            "subject_key": row.get("subject_key", "general"),
            "feature": "chat",
            "source_layer": "chat_history",
            "source_type": "chat_message",
            "timestamp": row.get("timestamp", ""),
            "language": row.get("language", ""),
            "topic": row.get("topic", ""),
            "learning_goal": row.get("learning_goal", ""),
            "source_name": "chat_history",
            "file_name": "messages.jsonl",
            "file_path_or_relative_path": relative_to_user(_messages_path(user_id, config), user_id, config),
            "modality": "text",
            "visibility": row.get("visibility", "user_visible"),
        }
        if text.strip():
            documents.append(LoadedDocument(text=text, metadata=metadata))
    return documents
