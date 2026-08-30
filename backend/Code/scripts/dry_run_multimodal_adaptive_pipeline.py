"""Dry-run multimodal and adaptive learning without external services."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.adaptive_learning import build_performance_context, choose_adaptive_difficulty
from src.chunking import chunk_documents
from src.config import load_config
from src.document_loaders import LoadedDocument
from src.performance_tracker import new_attempt, save_practice_attempt
from src.prompts import build_multimodal_chat_prompt
from src.subject_registry import build_subject_registry
from src.vector_store import InMemoryVectorStore


def main() -> int:
    """Demonstrate the multimodal adaptive prompt path with fake local data."""
    config = load_config(PROJECT_ROOT)
    subject = build_subject_registry(config)["spf_biology"]
    docs = [
        LoadedDocument("Selectable PDF text about DNA.", {"subject": subject.key, "source_name": "fake_onenote.pdf", "source_layer": "local_material", "page_number": 1, "modality": "pdf_text"}),
        LoadedDocument("OCR text: Zellkern contains DNA.", {"subject": subject.key, "source_name": "fake_onenote.pdf", "source_layer": "local_material", "page_number": 1, "modality": "ocr_text"}),
        LoadedDocument("Image description: labelled cell diagram with nucleus.", {"subject": subject.key, "source_name": "fake_onenote.pdf", "source_layer": "local_material", "page_number": 1, "modality": "page_image_description"}),
    ]
    chunks = chunk_documents(docs, chunk_size=120, overlap=20)
    store = InMemoryVectorStore()
    store.rebuild_collection(subject.collection_name, chunks)
    results = store.query(subject.collection_name, "DNA Zellkern", top_k=3)
    context = "\n".join(result.text for result in results)
    save_practice_attempt(new_attempt(subject_key=subject.key, topic="DNA", points_achieved=4, maximum_points=10, grade=3.0), config)
    difficulty = choose_adaptive_difficulty(subject.key, "DNA", config)
    performance = build_performance_context(subject.key, "DNA", config)
    prompt = build_multimodal_chat_prompt(subject, "German", "Erklaere DNA", context, "Official syllabus fake chunk", "", performance, audio_transcript="Audio fake transcript", image_ocr="OCR fake text", image_description="Image fake description")
    assert difficulty == "easy"
    assert "Source priority rules" in prompt
    assert "Audio fake transcript" in prompt
    print("PASS: fake multimodal documents chunked and retrieved")
    print("PASS: fake performance selected adaptive difficulty easy")
    print("PASS: multimodal adaptive prompt built")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
