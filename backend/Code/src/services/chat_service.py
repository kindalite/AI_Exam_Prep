"""Framework-neutral chat, RAG, multimodal, and persistence orchestration."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from ..audio_transcription import transcribe_audio_safe
from ..ai_metadata_store import AIProvenanceRecord, save_ai_provenance
from ..chat_history_store import new_chat_message, save_chat_media, save_chat_message
from ..config import AppConfig
from ..image_understanding import describe_image_safe
from ..llm_client import LLMResponse, generate_response
from ..model_providers import GenerationProvider, build_model_provider
from ..ocr import ocr_image_safe
from ..performance_tracker import new_attempt, save_practice_attempt
from ..prompts import build_multimodal_chat_prompt, build_system_prompt
from ..rag_memory_indexer import retrieve_user_memory
from ..retrieval import (
    StudyContext,
    build_vector_store,
    load_exam_criteria,
    load_learning_goals,
    retrieve_study_context,
    sources_to_context,
)
from ..subject_languages import language_name
from ..subject_registry import Subject, corpus_keys_for_request, get_subject
from ..user_data_paths import (
    get_user_subject_root,
    sanitize_username,
    user_memory_collection_name,
    user_subject_collection_name,
)
from ..vector_store import RetrievedChunk
from .identity_service import StudentContext
from .subject_service import list_learning_goals


@dataclass(frozen=True)
class ChatServiceResult:
    """All data produced by one chat request without any UI objects."""

    response: LLMResponse
    context: StudyContext
    prompt: str
    audio_transcript: str = ""
    image_ocr: str = ""
    image_description: str = ""
    warnings: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        """Return whether model generation succeeded."""
        return self.response.ok


def run_chat(
    *,
    subject: Subject,
    language: str,
    question: str,
    user_id: str,
    config: AppConfig,
    image_bytes: bytes | None = None,
    image_name: str | None = None,
    audio_bytes: bytes | None = None,
    audio_name: str | None = None,
    include_syllabus: bool = True,
    include_web: bool = False,
    include_performance: bool = True,
    persist_history: bool = True,
    retrieve: Callable[..., StudyContext] = retrieve_study_context,
    call_llm: Callable[..., LLMResponse] = generate_response,
) -> ChatServiceResult:
    """Run the existing chat workflow with explicit request context.

    The default retrieval path intentionally preserves current Streamlit
    behavior in this extraction stage. The identity/scoping stage replaces it
    with user-scoped retrieval before HTTP exposure.
    """
    warnings: list[str] = []
    image_ocr = ""
    image_description = ""
    audio_transcript = ""

    if image_bytes is not None:
        image_path = save_chat_media(image_bytes, image_name or "image", user_id, "image", config)
        image_ocr, warning = ocr_image_safe(image_path, config.ocr_languages)
        if warning:
            warnings.append(warning)
        image_description, warning = describe_image_safe(image_path, subject.key, config)
        if warning:
            warnings.append(warning)

    if audio_bytes is not None:
        audio_path = save_chat_media(audio_bytes, audio_name or "audio", user_id, "audio", config)
        audio_transcript, warning = transcribe_audio_safe(audio_path, config)
        if warning:
            warnings.append(warning)

    search_query = "\n".join(
        part for part in [question, audio_transcript, image_ocr, image_description] if part
    ).strip()
    context = retrieve(
        subject,
        search_query or subject.display_name,
        config=config,
        include_syllabus=include_syllabus,
        include_web=include_web,
        include_performance=include_performance,
    )
    prompt = build_multimodal_chat_prompt(
        subject,
        language,
        question,
        context.local_context,
        context.syllabus_context,
        context.web_context,
        context.performance_context,
        load_learning_goals(subject),
        load_exam_criteria(subject),
        audio_transcript,
        image_ocr,
        image_description,
        warnings + context.warnings,
    )
    response = call_llm(prompt, build_system_prompt(subject, language), config=config)

    if response.ok and persist_history:
        source_ids = [str(source.metadata.get("chunk_id", "")) for source in context.sources]
        source_layers = [str(source.metadata.get("source_layer", "")) for source in context.sources]
        save_practice_attempt(
            new_attempt(
                subject_key=subject.key,
                topic=question[:80],
                feature="chat",
                difficulty="adaptive",
                question=question,
                model_feedback=response.text,
                source_chunk_ids=source_ids,
            ),
            config,
        )
        save_chat_message(
            new_chat_message(
                user_id=user_id,
                subject_key=subject.key,
                language=language,
                user_text=question,
                audio_transcript=audio_transcript or None,
                image_ocr=image_ocr or None,
                image_description=image_description or None,
                assistant_answer=response.text,
                source_chunk_ids=source_ids,
                source_layers=source_layers,
                topic=question[:80],
            ),
            config,
        )

    combined_warnings = tuple(warnings + context.warnings)
    return ChatServiceResult(
        response=response,
        context=context,
        prompt=prompt,
        audio_transcript=audio_transcript,
        image_ocr=image_ocr,
        image_description=image_description,
        warnings=combined_warnings,
    )


class ChatModelUnavailableError(RuntimeError):
    """The configured model did not produce a usable answer."""


class ChatLearningGoalError(ValueError):
    """A requested learning goal is not valid for the selected scope."""


@dataclass(frozen=True)
class ApiChatResult:
    """Framework-neutral result for one non-streaming API chat request."""

    message_id: str
    answer: str
    sources: tuple[RetrievedChunk, ...]
    exam_tip: str | None
    used_model: str
    chunks_considered: int
    collection_names: tuple[str, ...]
    material_ids: tuple[str, ...]
    learning_goal_id: str | None
    created_at: datetime


def query_scoped_collection(
    store,
    collection_name: str,
    question: str,
    *,
    top_k: int,
    student_id: str | None = None,
    material_ids: tuple[str, ...] = (),
) -> list[RetrievedChunk]:
    """Query one collection with exact identity/material filters."""
    results: list[RetrievedChunk] = []
    filters = material_ids or (None,)
    for material_id in filters:
        clauses = []
        if student_id is not None:
            clauses.append({"user_id": student_id})
        if material_id is not None:
            clauses.append({"material_id": material_id})
        if len(clauses) > 1:
            where = {"$and": clauses}
        elif clauses:
            where = clauses[0]
        else:
            where = None
        queried = store.query(collection_name, question, top_k=top_k, where=where)
        for source in queried:
            metadata = dict(source.metadata)
            metadata["collection_name"] = collection_name
            results.append(RetrievedChunk(source.text, metadata, source.score))
    deduplicated: dict[tuple[str, str, str], RetrievedChunk] = {}
    for source in results:
        key = (
            collection_name,
            str(source.metadata.get("chunk_id", "")),
            source.text,
        )
        existing = deduplicated.get(key)
        if existing is None or source.score > existing.score:
            deduplicated[key] = source
    return sorted(deduplicated.values(), key=lambda item: item.score, reverse=True)


def read_scoped_file(
    student_id: str,
    corpus_keys: tuple[str, ...],
    config: AppConfig,
    filename: str,
) -> str:
    """Read a student's non-placeholder file, otherwise canonical content."""
    sections: list[str] = []
    for corpus_key in corpus_keys:
        subject = get_subject(corpus_key, config)
        user_path = get_user_subject_root(student_id, corpus_key, config) / filename
        canonical_path = (
            subject.learning_goals_file if filename == "learning_goals.md" else subject.exam_criteria_file
        )
        user_text = user_path.read_text(encoding="utf-8", errors="replace") if user_path.exists() else ""
        if user_text and "Add learning goals here." not in user_text and "Add exam criteria here." not in user_text:
            text = user_text
        else:
            text = canonical_path.read_text(encoding="utf-8", errors="replace") if canonical_path.exists() else ""
        if text.strip():
            sections.append(text.strip())
    return "\n\n".join(sections)


def learning_goal_context(
    *,
    config: AppConfig,
    student_id: str,
    subject_id: str,
    component_subject_id: str | None,
    learning_goal_id: str | None,
) -> str:
    """Resolve and, when requested, strictly scope parsed learning goals."""
    goals = list_learning_goals(
        config,
        subject_id,
        component_subject_id=component_subject_id,
        student_id=student_id,
    )
    if learning_goal_id is not None:
        goals = [goal for goal in goals if goal.learning_goal_id == learning_goal_id]
        if not goals:
            raise ChatLearningGoalError(
                "learning_goal_id does not belong to the selected student/subject scope"
            )
    return "\n".join(f"- [{goal.learning_goal_id}] {goal.text}" for goal in goals)


def _exam_tip(criteria: str) -> str | None:
    """Extract one honest concise tip from explicit exam criteria."""
    for raw_line in criteria.splitlines():
        line = raw_line.strip().lstrip("-*# ").strip()
        if not line or line.lower().startswith("exam criteria") or line.lower().startswith("add "):
            continue
        return f"Exam focus: {line[:220]}"
    return None


@dataclass(frozen=True)
class ScopedEvidence:
    """Private/canonical evidence and memory resolved for one student scope."""

    sources: tuple[RetrievedChunk, ...]
    memory_sources: tuple[RetrievedChunk, ...]
    chunks_considered: int
    collection_names: tuple[str, ...]


@dataclass(frozen=True)
class PreparedApiChat:
    """Validated retrieval and prompt state shared by JSON and SSE modes."""

    subject_id: str
    component_subject_id: str | None
    language: str
    question: str
    learning_goal_id: str | None
    prompt: str
    system_prompt: str
    evidence: tuple[RetrievedChunk, ...]
    scoped: ScopedEvidence
    exam_tip: str | None


def retrieve_scoped_evidence(
    *,
    subject_id: str,
    component_subject_id: str | None,
    question: str,
    material_ids: list[str],
    top_k: int,
    student: StudentContext,
    config: AppConfig,
    vector_store=None,
    memory_retriever: Callable[..., list[RetrievedChunk]] = retrieve_user_memory,
) -> ScopedEvidence:
    """Retrieve isolated user material, canonical material, and current-user memory."""
    safe_student = sanitize_username(student.student_id)
    corpus_keys = corpus_keys_for_request(subject_id, component_subject_id)
    store = vector_store or build_vector_store(config)
    requested_materials = tuple(dict.fromkeys(material_ids))
    collection_names: list[str] = []
    private_sources: list[RetrievedChunk] = []
    canonical_sources: list[RetrievedChunk] = []
    memory_sources: list[RetrievedChunk] = []
    for corpus_key in corpus_keys:
        private_collection = user_subject_collection_name(safe_student, corpus_key)
        canonical_collection = get_subject(corpus_key, config).collection_name
        collection_names.extend((private_collection, canonical_collection))
        private_sources.extend(
            query_scoped_collection(
                store,
                private_collection,
                question,
                top_k=top_k,
                student_id=safe_student,
                material_ids=requested_materials,
            )
        )
        canonical_sources.extend(
            query_scoped_collection(
                store,
                canonical_collection,
                question,
                top_k=top_k,
                material_ids=requested_materials,
            )
        )
        memory_collection = user_memory_collection_name(safe_student, corpus_key)
        collection_names.append(memory_collection)
        memory_sources.extend(
            memory_retriever(
                safe_student,
                corpus_key,
                question,
                config,
                vector_store=store,
                top_k=min(top_k, 4),
            )
        )
    considered = len(private_sources) + len(canonical_sources) + len(memory_sources)
    return ScopedEvidence(
        sources=tuple((private_sources + canonical_sources)[:top_k]),
        memory_sources=tuple(memory_sources[: min(top_k, 4)]),
        chunks_considered=considered,
        collection_names=tuple(collection_names),
    )


def prepare_api_chat(
    *,
    subject_id: str,
    component_subject_id: str | None,
    language: str,
    question: str,
    learning_goal_id: str | None,
    material_ids: list[str],
    top_k: int,
    student: StudentContext,
    config: AppConfig,
    vector_store=None,
    memory_retriever: Callable[..., list[RetrievedChunk]] = retrieve_user_memory,
) -> PreparedApiChat:
    """Validate scope, retrieve evidence, and build the prompt before generation."""
    safe_student = sanitize_username(student.student_id)
    corpus_keys = corpus_keys_for_request(subject_id, component_subject_id)
    scoped = retrieve_scoped_evidence(
        subject_id=subject_id,
        component_subject_id=component_subject_id,
        question=question,
        material_ids=material_ids,
        top_k=top_k,
        student=student,
        config=config,
        vector_store=vector_store,
        memory_retriever=memory_retriever,
    )
    subject = get_subject(subject_id, config)
    goals = learning_goal_context(
        config=config,
        student_id=safe_student,
        subject_id=subject_id,
        component_subject_id=component_subject_id,
        learning_goal_id=learning_goal_id,
    )
    criteria = read_scoped_file(safe_student, corpus_keys, config, "exam_criteria.md")
    evidence = scoped.sources
    prompt = build_multimodal_chat_prompt(
        subject,
        language_name(language),
        question,
        sources_to_context(list(evidence)),
        "",
        "",
        sources_to_context(list(scoped.memory_sources)),
        goals,
        criteria,
        warnings=[
            "No matching material chunks were found for the requested scope."
            if not evidence
            else ""
        ],
        config=config,
    )
    return PreparedApiChat(
        subject_id=subject_id,
        component_subject_id=component_subject_id,
        language=language,
        question=question,
        learning_goal_id=learning_goal_id,
        prompt=prompt,
        system_prompt=build_system_prompt(subject, language),
        evidence=evidence,
        scoped=scoped,
        exam_tip=_exam_tip(criteria),
    )


def finalize_api_chat(
    prepared: PreparedApiChat,
    answer: str,
    *,
    student: StudentContext,
    config: AppConfig,
    thread_id: str | None,
    metadata_writer: Callable[[AIProvenanceRecord, AppConfig], dict] = save_ai_provenance,
) -> ApiChatResult:
    """Create final metadata and non-authoritative provenance after one generation."""
    if not answer.strip():
        raise ChatModelUnavailableError("The model returned an empty answer")
    safe_student = sanitize_username(student.student_id)
    created_at = datetime.now(timezone.utc)
    correlation_seed = "|".join(
        [
            safe_student,
            prepared.subject_id,
            prepared.component_subject_id or "",
            prepared.question,
            created_at.isoformat(),
        ]
    )
    message_id = "ai_" + hashlib.sha256(correlation_seed.encode("utf-8")).hexdigest()[:24]
    used_material_ids = tuple(
        dict.fromkeys(
            str(source.metadata["material_id"])
            for source in prepared.evidence
            if source.metadata.get("material_id")
        )
    )
    if thread_id:
        source_ids = tuple(
            str(
                source.metadata.get("source_id")
                or source.metadata.get("chunk_id")
                or "src_" + hashlib.sha256(source.text.encode("utf-8")).hexdigest()[:16]
            )
            for source in prepared.evidence
        )
        metadata_writer(
            AIProvenanceRecord(
                student_id=safe_student,
                thread_id=thread_id,
                python_message_id=message_id,
                source_ids=source_ids,
                material_ids=used_material_ids,
                used_model=config.generation_model,
                provider=config.model_provider,
                retrieval_summary={
                    "chunks_considered": prepared.scoped.chunks_considered,
                    "chunks_used": len(prepared.evidence),
                    "collection_names": list(prepared.scoped.collection_names),
                    "material_ids": list(used_material_ids),
                    "learning_goal_id": prepared.learning_goal_id,
                },
                subject_id=prepared.subject_id,
                component_subject_id=prepared.component_subject_id,
                language=prepared.language,
                generated_at=created_at.isoformat().replace("+00:00", "Z"),
            ),
            config,
        )
    return ApiChatResult(
        message_id=message_id,
        answer=answer.strip(),
        sources=prepared.evidence,
        exam_tip=prepared.exam_tip,
        used_model=config.generation_model,
        chunks_considered=prepared.scoped.chunks_considered,
        collection_names=prepared.scoped.collection_names,
        material_ids=used_material_ids,
        learning_goal_id=prepared.learning_goal_id,
        created_at=created_at,
    )


def open_api_chat_stream(
    prepared: PreparedApiChat,
    *,
    config: AppConfig,
    provider: GenerationProvider | None = None,
):
    """Open one provider token iterator without making a non-streaming model call."""
    selected = provider or build_model_provider(config)
    if not getattr(selected, "supports_streaming", False):
        raise ChatModelUnavailableError(
            f"Provider {config.model_provider!r} does not support token streaming"
        )
    return iter(selected.stream(prepared.prompt, prepared.system_prompt))


def prefetch_api_chat_token(iterator) -> tuple[bool, str]:
    """Fetch one token so pre-token provider failures can remain normal HTTP errors."""
    try:
        token = next(iterator)
    except StopIteration:
        return False, ""
    except Exception as exc:
        raise ChatModelUnavailableError(
            f"Streaming provider failed before the first token: {exc.__class__.__name__}"
        ) from exc
    if not str(token):
        return prefetch_api_chat_token(iterator)
    return True, str(token)


def run_api_chat(
    *,
    subject_id: str,
    component_subject_id: str | None,
    language: str,
    question: str,
    learning_goal_id: str | None,
    material_ids: list[str],
    top_k: int,
    student: StudentContext,
    config: AppConfig,
    thread_id: str | None = None,
    vector_store=None,
    call_llm: Callable[..., LLMResponse] = generate_response,
    memory_retriever: Callable[..., list[RetrievedChunk]] = retrieve_user_memory,
    metadata_writer: Callable[[AIProvenanceRecord, AppConfig], dict] = save_ai_provenance,
) -> ApiChatResult:
    """Answer one API turn from isolated private, canonical, and student-memory context.

    This service deliberately does not persist chat messages. Supabase owns the
    authoritative Stage-1 transcript. Only privacy-minimal provenance is stored
    when a thread correlation ID is supplied.
    """
    prepared = prepare_api_chat(
        subject_id=subject_id,
        component_subject_id=component_subject_id,
        language=language,
        question=question,
        learning_goal_id=learning_goal_id,
        material_ids=material_ids,
        top_k=top_k,
        student=student,
        config=config,
        vector_store=vector_store,
        memory_retriever=memory_retriever,
    )
    response = call_llm(prepared.prompt, prepared.system_prompt, config=config)
    if not response.ok or not response.text.strip():
        raise ChatModelUnavailableError(response.error or "The model returned an empty answer")
    return finalize_api_chat(
        prepared,
        response.text,
        student=student,
        config=config,
        thread_id=thread_id,
        metadata_writer=metadata_writer,
    )
