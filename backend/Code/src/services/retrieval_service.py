"""User-isolated retrieval orchestration for future API handlers."""

from __future__ import annotations

from dataclasses import dataclass

from ..chunking import chunk_documents
from ..config import AppConfig
from ..document_loaders import load_subject_documents
from ..rag_memory_indexer import index_user_memory_for_subject, retrieve_user_memory
from ..retrieval import (
    StudyContext,
    build_user_subject_index,
    retrieve_for_user_subject,
    sources_to_context,
)
from ..source_policy import is_trusted_source
from ..subject_registry import corpus_keys_for_request, get_subject
from ..vector_store import InMemoryVectorStore, RetrievedChunk
from ..web_retrieval import search_web
from .identity_service import StudentContext


@dataclass(frozen=True)
class ScopedRetrievalResult:
    """User-scoped layered context plus resolved public/corpus identities."""

    subject_id: str
    component_subject_id: str | None
    corpus_keys: tuple[str, ...]
    context: StudyContext


def _copy_with_layer(source: RetrievedChunk, default_layer: str) -> RetrievedChunk:
    """Copy a source while supplying a missing source layer."""
    metadata = dict(source.metadata)
    previous_layer = metadata.get("source_layer")
    if previous_layer and previous_layer != default_layer:
        metadata["source_sub_layer"] = previous_layer
    metadata["source_layer"] = default_layer
    return RetrievedChunk(source.text, metadata, source.score)


def _matches_requested_metadata(
    source: RetrievedChunk,
    material_ids: set[str],
    learning_goal_id: str | None,
) -> bool:
    """Apply optional filters only to metadata carried by indexed chunks."""
    metadata = source.metadata
    if material_ids:
        candidates = {
            str(metadata.get(key, ""))
            for key in ("material_id", "source_id", "chunk_id", "source_name")
        }
        if not candidates.intersection(material_ids):
            return False
    if learning_goal_id and str(metadata.get("learning_goal_id", "")) != learning_goal_id:
        return False
    return True


def _canonical_sources(subject_key: str, config: AppConfig, query: str, top_k: int) -> tuple[list[RetrievedChunk], list[RetrievedChunk]]:
    """Retrieve approved shared goals/criteria and syllabus without shared notes."""
    subject = get_subject(subject_key, config)
    local_documents = load_subject_documents(
        subject.key,
        [subject.learning_goals_file, subject.exam_criteria_file, subject.criteria_dir],
        config=config,
    )
    syllabus_documents = load_subject_documents(subject.key, [subject.syllabus_dir], config=config)
    for document in local_documents:
        source_name = str(document.metadata.get("source_name", ""))
        document.metadata["source_layer"] = (
            "learning_goals" if source_name == "learning_goals.md" else "exam_criteria"
        )
    for document in syllabus_documents:
        document.metadata["source_layer"] = "official_syllabus"

    def rank(documents, collection: str) -> list[RetrievedChunk]:
        chunks = chunk_documents(documents, config.chunk_size, config.chunk_overlap)
        if not chunks:
            return []
        store = InMemoryVectorStore()
        store.rebuild_collection(collection, chunks)
        return store.query(collection, query, top_k=top_k)

    return (
        rank(local_documents, f"canonical_{subject.key}"),
        rank(syllabus_documents, f"syllabus_{subject.key}"),
    )


def index_student_subject(
    student: StudentContext,
    subject_id: str,
    config: AppConfig,
    *,
    component_subject_id: str | None = None,
    vector_store=None,
) -> dict:
    """Build only the resolved student's concrete subject collection(s)."""
    corpus_keys = corpus_keys_for_request(subject_id, component_subject_id)
    counts: dict[str, int] = {}
    for corpus_key in corpus_keys:
        counts[corpus_key] = build_user_subject_index(
            student.student_id,
            get_subject(corpus_key, config),
            config,
            vector_store=vector_store,
        )
    return {"student_id": student.student_id, "corpus_keys": corpus_keys, "indexed_chunks": counts}


def index_student_memory(
    student: StudentContext,
    subject_id: str,
    config: AppConfig,
    *,
    component_subject_id: str | None = None,
    vector_store=None,
) -> dict[str, dict]:
    """Index the student's history separately for each resolved corpus."""
    return {
        key: index_user_memory_for_subject(
            student.student_id,
            key,
            config,
            vector_store=vector_store,
        )
        for key in corpus_keys_for_request(subject_id, component_subject_id)
    }


def retrieve_student_study_context(
    student: StudentContext,
    subject_id: str,
    query: str,
    config: AppConfig,
    *,
    component_subject_id: str | None = None,
    material_ids: list[str] | None = None,
    learning_goal_id: str | None = None,
    include_shared: bool = True,
    include_memory: bool = True,
    include_web: bool = False,
    top_k: int = 6,
    vector_store=None,
) -> ScopedRetrievalResult:
    """Return strictly user-scoped material plus approved shared/public layers."""
    corpus_keys = corpus_keys_for_request(subject_id, component_subject_id)
    requested_material_ids = set(material_ids or [])
    user_sources: list[RetrievedChunk] = []
    canonical_sources: list[RetrievedChunk] = []
    syllabus_sources: list[RetrievedChunk] = []
    memory_sources: list[RetrievedChunk] = []
    web_sources: list[RetrievedChunk] = []
    warnings: list[str] = []

    for corpus_key in corpus_keys:
        subject = get_subject(corpus_key, config)
        retrieved = retrieve_for_user_subject(
            student.student_id,
            subject,
            query,
            config,
            vector_store=vector_store,
            top_k=max(top_k, 24) if requested_material_ids or learning_goal_id else top_k,
        )
        user_sources.extend(
            _copy_with_layer(source, "user_material")
            for source in retrieved.sources
            if _matches_requested_metadata(source, requested_material_ids, learning_goal_id)
        )

        if include_shared:
            local_shared, syllabus_shared = _canonical_sources(corpus_key, config, query, top_k)
            canonical_sources.extend(local_shared)
            syllabus_sources.extend(syllabus_shared)

        if include_memory:
            memory_sources.extend(
                _copy_with_layer(source, "student_memory")
                for source in retrieve_user_memory(
                    student.student_id,
                    corpus_key,
                    query,
                    config,
                    vector_store=vector_store,
                    top_k=top_k,
                )
            )

    if include_web and config.allow_internet:
        try:
            public_subject = get_subject(corpus_keys[0], config).display_name
            public_query = f"Kantonsschule Alpenquai Luzern {public_subject} Lehrplan"
            for source in search_web(public_query, config, config.max_web_results):
                if is_trusted_source(source.url, source.title):
                    web_sources.append(
                        RetrievedChunk(
                            source.text,
                            {
                                "source_name": source.title,
                                "url": source.url,
                                "source_layer": "public_web",
                            },
                            1.0,
                        )
                    )
        except Exception as exc:
            warnings.append(f"Public web retrieval unavailable: {exc}")

    user_sources = sorted(user_sources, key=lambda source: source.score, reverse=True)[:top_k]
    canonical_sources = sorted(canonical_sources, key=lambda source: source.score, reverse=True)[:top_k]
    syllabus_sources = sorted(syllabus_sources, key=lambda source: source.score, reverse=True)[:top_k]
    memory_sources = sorted(memory_sources, key=lambda source: source.score, reverse=True)[:top_k]
    all_sources = user_sources + canonical_sources + syllabus_sources + memory_sources + web_sources
    context = StudyContext(
        local_context=sources_to_context(user_sources + canonical_sources),
        syllabus_context=sources_to_context(syllabus_sources),
        web_context=sources_to_context(web_sources),
        performance_context=sources_to_context(memory_sources),
        sources=all_sources,
        warnings=warnings,
        missing_material_detected=not user_sources,
    )
    return ScopedRetrievalResult(
        subject_id=subject_id,
        component_subject_id=component_subject_id,
        corpus_keys=corpus_keys,
        context=context,
    )
