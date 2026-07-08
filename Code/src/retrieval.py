"""Retrieval pipeline that connects subject files, chunks, and vector stores."""

from __future__ import annotations

from dataclasses import dataclass

from .chunking import chunk_documents
from .config import AppConfig, load_config
from .document_loaders import load_subject_documents
from .subject_registry import Subject, get_subject
from .utils import read_text_if_exists
from .vector_store import ChromaVectorStore, InMemoryVectorStore, RetrievedChunk


@dataclass(frozen=True)
class RetrievalResult:
    """Context and source chunks prepared for an LLM prompt."""

    context: str
    sources: list[RetrievedChunk]
    message: str


def build_vector_store(config: AppConfig | None = None, in_memory: bool = False):
    """Create the vector store used by the app or tests."""
    app_config = config or load_config()
    if in_memory:
        return InMemoryVectorStore()
    try:
        return ChromaVectorStore(app_config.vector_db_dir, app_config.embedding_model)
    except RuntimeError:
        return InMemoryVectorStore()


def build_subject_index(subject: Subject, config: AppConfig | None = None, vector_store=None) -> int:
    """Load files for one subject and rebuild its vector collection."""
    app_config = config or load_config()
    store = vector_store or build_vector_store(app_config)
    folders = [subject.notes_dir, subject.syllabus_dir, subject.criteria_dir]
    documents = load_subject_documents(subject.key, folders)
    # Add core Markdown files even if they live outside notes/syllabus/criteria.
    for path in [subject.learning_goals_file, subject.exam_criteria_file]:
        if path.exists():
            documents.extend(load_subject_documents(subject.key, [path.parent]))
            break
    chunks = chunk_documents(documents, chunk_size=app_config.chunk_size, overlap=app_config.chunk_overlap)
    return store.rebuild_collection(subject.collection_name, chunks)


def retrieve_for_subject(subject: Subject, question: str, vector_store=None, top_k: int = 4) -> RetrievalResult:
    """Retrieve source chunks for one subject and question."""
    store = vector_store or build_vector_store()
    sources = store.query(subject.collection_name, question, top_k=top_k)
    if not sources:
        message = "No indexed notes were found yet. Add material and build the subject database first."
        return RetrievalResult(context="", sources=[], message=message)
    context_lines = []
    for index, source in enumerate(sources, start=1):
        name = source.metadata.get("source_name", "unknown source")
        context_lines.append(f"[Source {index}: {name}]\n{source.text}")
    return RetrievalResult(context="\n\n".join(context_lines), sources=sources, message="Sources retrieved.")


def load_learning_goals(subject: Subject) -> str:
    """Read the learning goals file for a subject."""
    return read_text_if_exists(subject.learning_goals_file)


def load_exam_criteria(subject: Subject) -> str:
    """Read the exam criteria file for a subject."""
    return read_text_if_exists(subject.exam_criteria_file)


def retrieve_by_subject_key(subject_key: str, question: str, top_k: int = 4) -> RetrievalResult:
    """Convenience function for retrieving by subject key."""
    return retrieve_for_subject(get_subject(subject_key), question, top_k=top_k)

