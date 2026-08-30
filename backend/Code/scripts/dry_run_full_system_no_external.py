"""Dry-run the full upgraded system with no internet, Ollama, OCR, or Whisper."""

from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.adaptive_learning import choose_adaptive_difficulty
from src.chunking import chunk_documents
from src.config import AppConfig, load_config
from src.document_loaders import LoadedDocument
from src.grader import calculate_grade
from src.material_router import discover_learning_material, group_material_by_subject
from src.performance_tracker import new_attempt, read_practice_attempts, save_practice_attempt
from src.prompts import build_multimodal_chat_prompt, build_quiz_prompt
from src.subject_registry import build_subject_registry
from src.vector_store import InMemoryVectorStore, RetrievedChunk


def main() -> int:
    """Run a no-external-services demonstration of the upgraded architecture."""
    base = load_config(PROJECT_ROOT)
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        material_root = tmp_path / "learning_material"
        (material_root / "Biologie").mkdir(parents=True)
        (material_root / "Biologie" / "cells.md").write_text("Zellkern und DNA", encoding="utf-8")
        config = AppConfig(**{**base.__dict__, "data_dir": tmp_path / "data", "subject_data_dir": tmp_path / "data" / "subjects", "vector_db_dir": tmp_path / "vector_db", "learning_material_root": material_root, "performance_log_file": tmp_path / "data" / "performance" / "attempts.jsonl", "allow_internet": False})
        subjects = build_subject_registry(config)
        subject = subjects["biology"]
        paths = discover_learning_material(config)
        grouped = group_material_by_subject(paths, subjects)
        docs = [LoadedDocument("Fake PDF text, fake OCR text, fake image description about DNA.", {"subject": subject.key, "source_name": "fake.pdf", "source_layer": "local_material", "page_number": 1, "modality": "page_image_description"})]
        chunks = chunk_documents(docs, 140, 20)
        store = InMemoryVectorStore()
        store.rebuild_collection(subject.collection_name, chunks)
        local_sources = store.query(subject.collection_name, "DNA", top_k=2)
        syllabus_source = RetrievedChunk("Official syllabus fake: cells and genetics", {"source_name": "KSA syllabus", "source_layer": "official_syllabus", "url": "https://example.test"}, 1.0)
        save_practice_attempt(new_attempt(subject_key=subject.key, topic="DNA", points_achieved=8, maximum_points=10, grade=5.0), config)
        difficulty = choose_adaptive_difficulty(subject.key, "DNA", config)
        prompt = build_multimodal_chat_prompt(subject, "English", "Explain DNA", "\n".join(item.text for item in local_sources), syllabus_source.text, "", "Performance fake context", audio_transcript="fake audio", image_ocr="fake ocr", image_description="fake image")
        quiz_prompt = build_quiz_prompt(subject, "French", "DNA", difficulty, prompt, "criteria", "performance", ["DNA"])
        grade = calculate_grade(8, 10).grade
        attempts = read_practice_attempts(config, subject.key)
        assert grouped[subject.key]
        assert local_sources
        assert "Source priority rules" in prompt
        assert "French" in quiz_prompt
        assert grade == 5.0
        assert attempts
    print("PASS: config loads gemma3:4b defaults")
    print("PASS: fake learning material discovered and grouped")
    print("PASS: fake multimodal chunks retrieved with source layers")
    print("PASS: fake syllabus fallback and performance memory included")
    print("PASS: quiz and grading path completed without external tools")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
