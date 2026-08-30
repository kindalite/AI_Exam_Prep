"""Dry-run the RAG pipeline without calling Ollama."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.chunking import chunk_documents
from src.document_loaders import load_document
from src.prompts import build_chat_prompt, build_grading_prompt, build_quiz_prompt
from src.subject_registry import build_subject_registry
from src.vector_store import InMemoryVectorStore


def main() -> int:
    """Run a small pipeline with sample biology data and print the generated prompts."""
    subject = build_subject_registry()["spf_biology"]
    sample_file = PROJECT_ROOT / "test_data" / "biology_sample.md"
    documents = load_document(sample_file, subject.key)
    chunks = chunk_documents(documents, chunk_size=180, overlap=30)

    store = InMemoryVectorStore()
    store.rebuild_collection(subject.collection_name, chunks)
    results = store.query(subject.collection_name, "cell nucleus DNA", top_k=2)
    context = "\n\n".join(result.text for result in results)

    print("DRY RUN: retrieved chunks")
    for result in results:
        print(f"- {result.metadata.get('source_name')} score={result.score:.2f}")

    print("\nCHAT PROMPT\n")
    print(build_chat_prompt(subject, "German", "Was ist die Aufgabe des Zellkerns?", context, "Cell learning goal", "Use source material."))

    print("\nQUIZ PROMPT\n")
    print(build_quiz_prompt(subject, "German", "Cell structure", "medium", context, "Use source material."))

    print("\nGRADING PROMPT\n")
    print(build_grading_prompt(subject, "German", "Explain the nucleus.", "It stores DNA.", 4, "2p DNA, 2p control center", context, "Use source material."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
