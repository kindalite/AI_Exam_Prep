"""Dry-run the full local student workflow with fakes only."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.adaptive_learning import choose_adaptive_difficulty
from src.chat_history_store import new_chat_message, save_chat_message
from src.config import load_config
from src.rag_memory_indexer import index_user_memory_for_subject
from src.timed_practice import start_practice_attempt, submit_and_grade_attempt
from src.token_budget import ContextSection, budget_context_sections
from src.user_manager import authenticate_user, create_user
import src.ui_docs  # noqa: F401
import src.ui_subject_dashboard  # noqa: F401


def main() -> int:
    base = load_config(PROJECT_ROOT)
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        config = replace(base, data_dir=tmp_path / "data", user_data_root=tmp_path / "data" / "users", auth_db_file=tmp_path / "data" / "auth" / "users.json", vector_db_dir=tmp_path / "vector_db", subject_data_dir=tmp_path / "data" / "subjects", allow_internet=False)
        user = create_user("full", "pw", config)
        assert authenticate_user("full", "pw", config)
        save_chat_message(new_chat_message(user_id=user["user_id"], subject_key="german", user_text="fake chat", audio_transcript="fake audio", image_ocr="fake ocr", image_description="fake image"), config)
        session, _practice, _solution = start_practice_attempt(user["user_id"], "german", "quiz", "German", "Essay", "adaptive", "easy", 1, "Q\n## Solutions\nA", config)
        submit_and_grade_attempt(session, "answer", 4, 10, ["started"], ["needs structure"], ["review outline"], config)
        index_user_memory_for_subject(user["user_id"], "german", config)
        assert choose_adaptive_difficulty("german", "Essay", config) in {"easy", "medium", "hard"}
        budgeted = budget_context_sections([ContextSection("question", "Q", 1), ContextSection("web", "web " * 100000, 7)], config)
        assert budgeted.estimated_tokens < config.gemma_max_context_tokens
    print("PASS: environment config loads")
    print("PASS: user login/register and isolated metadata save")
    print("PASS: quiz grading, performance report, RAG indexing, adaptive difficulty")
    print("PASS: token budget protection and docs module imports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
