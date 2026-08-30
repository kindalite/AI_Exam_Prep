"""Retrieval pipeline that connects subject files, chunks, web sources, and performance memory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .adaptive_learning import build_performance_context
from .chunking import chunk_documents
from .config import AppConfig, load_config
from .document_loaders import load_subject_documents
from .material_router import discover_learning_material, group_material_by_subject
from .material_manifest import load_manifest, stable_material_id
from .subject_registry import Subject, corpus_subjects, get_subject
from .user_data_paths import get_user_subject_root, sanitize_username, user_subject_collection_name
from .utils import read_text_if_exists
from .vector_store import ChromaVectorStore, InMemoryVectorStore, RetrievedChunk


@dataclass(frozen=True)
class RetrievalResult:
    """Context and source chunks prepared for an LLM prompt."""

    context: str
    sources: list[RetrievedChunk]
    message: str


@dataclass(frozen=True)
class StudyContext:
    """Layered source context for source-grounded studying."""

    local_context: str
    syllabus_context: str
    web_context: str
    performance_context: str
    sources: list[RetrievedChunk]
    warnings: list[str]
    missing_material_detected: bool


def build_vector_store(config: AppConfig | None = None, in_memory: bool = False):
    """Create the vector store used by the app or tests."""
    app_config = config or load_config()
    if in_memory:
        return InMemoryVectorStore()
    try:
        return ChromaVectorStore(app_config.vector_db_dir, app_config.embedding_model)
    except RuntimeError:
        return InMemoryVectorStore()


def _external_material_for_subject(subject: Subject, config: AppConfig) -> list:
    """Return external learning-material paths guessed for one subject."""
    subjects = corpus_subjects(config)
    grouped = group_material_by_subject(discover_learning_material(config), subjects)
    return grouped.get(subject.key, [])


def build_subject_index(subject: Subject, config: AppConfig | None = None, vector_store=None) -> int:
    """Load files for one subject and rebuild its vector collection."""
    app_config = config or load_config()
    store = vector_store or build_vector_store(app_config)
    if subject.is_virtual:
        return sum(
            build_subject_index(get_subject(key, app_config), app_config, vector_store=store)
            for key in subject.components
        )
    folders = [subject.notes_dir, subject.syllabus_dir, subject.criteria_dir]
    for legacy_key in subject.legacy_storage_keys:
        legacy_root = app_config.subject_data_dir / legacy_key
        folders.extend([legacy_root / "notes", legacy_root / "syllabus", legacy_root / "criteria"])
    folders.extend(_external_material_for_subject(subject, app_config))
    documents = load_subject_documents(subject.key, folders, config=app_config)
    for path in [subject.learning_goals_file, subject.exam_criteria_file]:
        if path.exists():
            documents.extend(load_subject_documents(subject.key, [path], config=app_config))
    for legacy_key in subject.legacy_storage_keys:
        legacy_root = app_config.subject_data_dir / legacy_key
        for path in [legacy_root / "learning_goals.md", legacy_root / "exam_criteria.md"]:
            if path.exists():
                documents.extend(load_subject_documents(subject.key, [path], config=app_config))
    for document in documents:
        source_path = Path(str(document.metadata.get("source_path", "")))
        if source_path.name:
            document.metadata["material_id"] = stable_material_id(
                "canonical", subject.key, source_path
            )
        document.metadata["source_layer"] = "canonical"
    chunks = chunk_documents(documents, chunk_size=app_config.chunk_size, overlap=app_config.chunk_overlap)
    return store.rebuild_collection(subject.collection_name, chunks)


def _chunks_to_context(sources: list[RetrievedChunk]) -> str:
    """Format chunks as LLM context with source metadata."""
    context_lines = []
    for index, source in enumerate(sources, start=1):
        name = source.metadata.get("source_name", "unknown source")
        page = source.metadata.get("page_number")
        modality = source.metadata.get("modality")
        url = source.metadata.get("url")
        details = ", ".join(str(item) for item in [f"page {page}" if page else "", f"modality: {modality}" if modality else "", f"url: {url}" if url else ""] if item)
        context_lines.append(f"[Source {index}: {name}{' - ' + details if details else ''}]\n{source.text}")
    return "\n\n".join(context_lines)


def sources_to_context(sources: list[RetrievedChunk]) -> str:
    """Format retrieved sources as citation-friendly model context."""
    return _chunks_to_context(sources)


def retrieve_for_subject(subject: Subject, question: str, vector_store=None, top_k: int = 4) -> RetrievalResult:
    """Retrieve source chunks for one subject and question."""
    store = vector_store or build_vector_store()
    if subject.is_virtual:
        sources: list[RetrievedChunk] = []
        for component_key in subject.components:
            sources.extend(store.query(f"subject_{component_key}", question, top_k=top_k))
        sources = sorted(sources, key=lambda item: item.score, reverse=True)[:top_k]
        if not sources:
            return RetrievalResult("", [], "No indexed SPF component notes were found yet.")
        return RetrievalResult(_chunks_to_context(sources), sources, "SPF component sources retrieved.")
    sources = store.query(subject.collection_name, question, top_k=top_k)
    if not sources:
        message = "No indexed notes were found yet. Add material and build the subject database first."
        return RetrievalResult(context="", sources=[], message=message)
    return RetrievalResult(context=_chunks_to_context(sources), sources=sources, message="Sources retrieved.")



def build_user_subject_index(user_id: str, subject: Subject, config: AppConfig | None = None, vector_store=None) -> int:
    """Build a user-scoped subject index with user_id metadata on every chunk."""
    app_config = config or load_config()
    safe_user = sanitize_username(user_id)
    store = vector_store or build_vector_store(app_config)
    if subject.is_virtual:
        return sum(
            build_user_subject_index(safe_user, get_subject(key, app_config), app_config, vector_store=store)
            for key in subject.components
        )
    user_subject_root = get_user_subject_root(safe_user, subject.key, app_config)
    folders = [user_subject_root / "notes", user_subject_root / "syllabus", user_subject_root / "criteria", user_subject_root / "learning_goals.md", user_subject_root / "exam_criteria.md"]
    for legacy_key in subject.legacy_storage_keys:
        legacy_root = get_user_subject_root(safe_user, legacy_key, app_config)
        folders.extend([legacy_root / "notes", legacy_root / "syllabus", legacy_root / "criteria", legacy_root / "learning_goals.md", legacy_root / "exam_criteria.md"])
    documents = load_subject_documents(subject.key, folders, config=app_config)
    manifest_rows = load_manifest(user_subject_root / "material_manifest.jsonl")
    manifest_by_path = {
        str(row.get("source_path", "")): row for row in manifest_rows if row.get("source_path")
    }
    manifest_by_name = {
        str(row.get("stored_name") or row.get("source_name") or ""): row
        for row in manifest_rows
    }
    for document in documents:
        document.metadata["user_id"] = safe_user
        row = manifest_by_path.get(str(document.metadata.get("source_path", ""))) or manifest_by_name.get(
            str(document.metadata.get("source_name", ""))
        )
        if row:
            document.metadata.update(
                {
                    "material_id": str(row.get("material_id") or row.get("file_id") or ""),
                    "original_name": str(row.get("original_name") or row.get("source_name") or ""),
                    "section": str(row.get("section") or ""),
                    "language": str(row.get("language") or ""),
                }
            )
    chunks = chunk_documents(documents, chunk_size=app_config.chunk_size, overlap=app_config.chunk_overlap)
    for chunk in chunks:
        chunk.metadata["user_id"] = safe_user
    return store.rebuild_collection(user_subject_collection_name(safe_user, subject.key), chunks)


def retrieve_for_user_subject(user_id: str, subject: Subject, question: str, config: AppConfig | None = None, vector_store=None, top_k: int = 4) -> RetrievalResult:
    """Retrieve chunks from one user's isolated subject collection only."""
    app_config = config or load_config()
    safe_user = sanitize_username(user_id)
    store = vector_store or build_vector_store(app_config)
    if subject.is_virtual:
        sources: list[RetrievedChunk] = []
        for component_key in subject.components:
            component = get_subject(component_key, app_config)
            sources.extend(
                store.query(
                    user_subject_collection_name(safe_user, component.key),
                    question,
                    top_k=top_k,
                    where={"user_id": safe_user},
                )
            )
        sources = sorted(sources, key=lambda item: item.score, reverse=True)[:top_k]
        if not sources:
            return RetrievalResult("", [], "No indexed SPF component notes were found for this user yet.")
        return RetrievalResult(_chunks_to_context(sources), sources, "User-scoped SPF component sources retrieved.")
    sources = store.query(user_subject_collection_name(safe_user, subject.key), question, top_k=top_k, where={"user_id": safe_user})
    if not sources:
        return RetrievalResult(context="", sources=[], message="No indexed notes were found for this user and subject yet.")
    return RetrievalResult(context=_chunks_to_context(sources), sources=sources, message="User-scoped sources retrieved.")

def retrieve_study_context(
    subject: Subject,
    query: str,
    config: AppConfig | None = None,
    include_syllabus: bool = True,
    include_web: bool = False,
    include_performance: bool = True,
    top_k: int = 6,
    vector_store=None,
) -> StudyContext:
    """Return layered context for source-grounded studying."""
    app_config = config or load_config()
    local_result = retrieve_for_subject(subject, query, vector_store=vector_store, top_k=top_k)
    warnings: list[str] = []
    syllabus_context = ""
    web_context = ""
    sources = list(local_result.sources)
    missing = not local_result.sources

    if include_syllabus:
        try:
            from .syllabus_fetcher import ensure_subject_syllabus_cached, should_fetch_syllabus_for_subject

            if should_fetch_syllabus_for_subject(subject, local_result):
                syllabus_docs = ensure_subject_syllabus_cached(subject, app_config)
                syllabus_chunks = chunk_documents(syllabus_docs, chunk_size=app_config.chunk_size, overlap=app_config.chunk_overlap)
                syllabus_sources = [RetrievedChunk(chunk.text, dict(chunk.metadata), 1.0) for chunk in syllabus_chunks[:top_k]]
                syllabus_context = _chunks_to_context(syllabus_sources)
                sources.extend(syllabus_sources)
                missing = True
        except Exception as exc:
            warnings.append(f"Official syllabus fallback unavailable: {exc}")

    if include_web and getattr(app_config, "allow_internet", True):
        try:
            from .web_retrieval import search_web

            public_query = f"Kantonsschule Alpenquai Luzern 4. Klasse {subject.display_name} Lehrplan"
            web_sources = search_web(public_query, app_config, getattr(app_config, "max_web_results", 5))
            web_chunks = [RetrievedChunk(source.text, {"source_name": source.title, "url": source.url, "source_layer": "public_web"}, 1.0) for source in web_sources]
            web_context = _chunks_to_context(web_chunks)
            sources.extend(web_chunks)
        except Exception as exc:
            warnings.append(f"Public web retrieval unavailable: {exc}")

    performance_context = build_performance_context(subject.key, query, app_config) if include_performance else ""
    return StudyContext(local_result.context, syllabus_context, web_context, performance_context, sources, warnings, missing)


def load_learning_goals(subject: Subject) -> str:
    """Read the learning goals file for a subject."""
    if subject.is_virtual:
        subject_root = subject.learning_goals_file.parent.parent
        return "\n\n".join(
            text
            for key in subject.components
            if (text := read_text_if_exists(subject_root / key / "learning_goals.md"))
        )
    return read_text_if_exists(subject.learning_goals_file)


def load_exam_criteria(subject: Subject) -> str:
    """Read the exam criteria file for a subject."""
    if subject.is_virtual:
        subject_root = subject.exam_criteria_file.parent.parent
        return "\n\n".join(
            text
            for key in subject.components
            if (text := read_text_if_exists(subject_root / key / "exam_criteria.md"))
        )
    return read_text_if_exists(subject.exam_criteria_file)


def retrieve_by_subject_key(subject_key: str, question: str, top_k: int = 4) -> RetrievalResult:
    """Convenience function for retrieving by subject key."""
    return retrieve_for_subject(get_subject(subject_key), question, top_k=top_k)
