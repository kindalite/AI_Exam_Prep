"""Dry-run user-isolated RAG memory without external services."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.chat_history_store import new_chat_message, save_chat_message
from src.chunking import chunk_documents
from src.config import load_config
from src.rag_memory_indexer import build_rag_documents_from_user_history, index_user_memory_for_subject, retrieve_user_memory
from src.user_manager import create_user
from src.user_data_paths import get_user_subject_root
from src.vector_store import InMemoryVectorStore


def main() -> int:
    base = load_config(PROJECT_ROOT)
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        config = replace(base, data_dir=tmp_path / "data", user_data_root=tmp_path / "data" / "users", auth_db_file=tmp_path / "data" / "auth" / "users.json", subject_data_dir=tmp_path / "data" / "subjects")
        a = create_user("A", "pw", config)
        mat = get_user_subject_root(a["user_id"], "chemistry", config) / "notes" / "template.md"
        mat.write_text("Template chemistry material", encoding="utf-8")
        b = create_user("B", "pw", config, template_user_id=a["user_id"])
        save_chat_message(new_chat_message(user_id=a["user_id"], subject_key="chemistry", user_text="A private atom note"), config)
        save_chat_message(new_chat_message(user_id=b["user_id"], subject_key="chemistry", user_text="B private ion note"), config)
        assert mat.name in [p.name for p in (get_user_subject_root(b["user_id"], "chemistry", config) / "notes").iterdir()]
        store = InMemoryVectorStore()
        index_user_memory_for_subject(b["user_id"], "chemistry", config, vector_store=store)
        results = retrieve_user_memory(b["user_id"], "chemistry", "ion", config, vector_store=store)
        assert results and all(row.metadata["user_id"] == b["user_id"] for row in results)
        assert "A private" not in "\n".join(row.text for row in results)
        assert build_rag_documents_from_user_history(b["user_id"], config)
    print("PASS: template material copied")
    print("PASS: isolated chat history indexed")
    print("PASS: query only returned current user memory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
