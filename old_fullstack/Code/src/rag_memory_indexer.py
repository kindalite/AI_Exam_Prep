"""Build and index per-user chat, practice, and performance memory for RAG."""

from __future__ import annotations

import json
from pathlib import Path

from .chat_history_store import chat_messages_to_documents
from .chunking import chunk_documents
from .document_loaders import LoadedDocument
from .practice_store import practice_records_to_documents
from .retrieval import build_vector_store
from .user_data_paths import get_user_root, sanitize_username, user_memory_collection_name
from .utils import ensure_directory


def build_rag_documents_from_user_history(user_id: str, config) -> list[LoadedDocument]:
    """Build RAG documents from one user's chat/practice/performance history."""
    safe_user = sanitize_username(user_id)
    documents = chat_messages_to_documents(safe_user, config)
    documents.extend(practice_records_to_documents(safe_user, config))
    return documents


def export_user_memory_chunks(user_id: str, documents: list[LoadedDocument], config) -> dict:
    """Write RAG memory documents to JSONL files for transparent inspection."""
    root = get_user_root(user_id, config) / "rag_exports"
    ensure_directory(root)
    counts = {"chat_chunks": 0, "practice_chunks": 0, "performance_chunks": 0}
    files = {
        "chat_history": root / "chat_chunks.jsonl",
        "generated_quiz": root / "practice_chunks.jsonl",
        "generated_exam": root / "practice_chunks.jsonl",
        "performance_report": root / "performance_chunks.jsonl",
    }
    handles = {path: path.open("a", encoding="utf-8") for path in set(files.values())}
    try:
        for doc in documents:
            layer = str(doc.metadata.get("source_layer", "chat_history"))
            path = files.get(layer, root / "chat_chunks.jsonl")
            row = {"text": doc.text, "metadata": doc.metadata}
            handles[path].write(json.dumps(row, ensure_ascii=False) + "\n")
            if layer == "performance_report":
                counts["performance_chunks"] += 1
            elif layer.startswith("generated"):
                counts["practice_chunks"] += 1
            else:
                counts["chat_chunks"] += 1
    finally:
        for handle in handles.values():
            handle.close()
    return counts


def index_user_memory_for_subject(user_id: str, subject_key: str, config, vector_store=None) -> dict:
    """Index one user's memory for one subject into a user-scoped vector collection."""
    safe_user = sanitize_username(user_id)
    documents = [doc for doc in build_rag_documents_from_user_history(safe_user, config) if doc.metadata.get("subject_key") == subject_key or doc.metadata.get("subject") == subject_key]
    for doc in documents:
        doc.metadata["user_id"] = safe_user
    export_user_memory_chunks(safe_user, documents, config)
    chunks = chunk_documents(documents, chunk_size=getattr(config, "chunk_size", 900), overlap=getattr(config, "chunk_overlap", 150))
    store = vector_store or build_vector_store(config)
    collection = user_memory_collection_name(safe_user, subject_key)
    count = store.rebuild_collection(collection, chunks)
    return {"user_id": safe_user, "subject_key": subject_key, "collection_name": collection, "indexed_chunks": count}


def retrieve_user_memory(user_id: str, subject_key: str, query: str, config, vector_store=None, top_k: int = 4):
    """Retrieve memory chunks filtered by user_id for defense-in-depth isolation."""
    safe_user = sanitize_username(user_id)
    store = vector_store or build_vector_store(config)
    return store.query(user_memory_collection_name(safe_user, subject_key), query, top_k=top_k, where={"user_id": safe_user})
