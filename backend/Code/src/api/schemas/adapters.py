"""Adapters from existing backend dataclasses to API contract models."""

from __future__ import annotations

import hashlib
from dataclasses import asdict

from ...services.chat_service import ApiChatResult
from ...services.health_service import ApiHealthSnapshot, ModelStatusSnapshot
from ...services.grading_service import GradingApiResult
from ...services.mock_exam_service import MockExamApiResult
from ...services.quiz_service import QuizApiResult
from ...services.study_plan_service import StudyPlanApiResult
from ...services.material_service import MaterialInventoryItem
from ...services.subject_service import LearningGoalRecord, SubjectReadMetadata
from ...services.upload_service import DocumentImportResult
from ...subject_registry import Subject, get_subject
from ...vector_store import RetrievedChunk
from .chat import ChatResponse, RetrievalSummary, SourceSnippet
from .grading import GradingResult
from .health import BackendHealth, ModelStatus
from .materials import DocumentImportResponse, MaterialModel, MaterialSourceModel
from .mock_exam import MockExam, MockExamQuestion
from .quiz import Quiz, QuizQuestion
from .study_plan import StudyPlan, StudyPlanItem
from .subjects import SubjectComponentModel, SubjectModel
from .common import utc_now


def subject_to_model(subject: Subject, *, config=None) -> SubjectModel:
    """Convert a registry subject to its public API representation."""
    components = [
        SubjectComponentModel(
            subject_id=component.key,
            display_name=component.display_name,
            language=component.api_language,
        )
        for key in subject.components
        for component in [get_subject(key, config)]
    ]
    return SubjectModel(
        subject_id=subject.key,
        display_name=subject.display_name,
        language=subject.api_language,
        is_virtual=subject.is_virtual,
        components=components,
        corpus_keys=list(subject.components) if subject.is_virtual else [subject.key],
    )


def subject_with_metadata_to_model(
    subject: Subject,
    metadata: SubjectReadMetadata,
    *,
    config=None,
) -> SubjectModel:
    """Combine registry identity with truthful read/index metadata."""
    base = subject_to_model(subject, config=config)
    return base.model_copy(
        update={
            "corpus_keys": list(metadata.corpus_keys),
            "topics": list(metadata.topics),
            "indexed_materials": metadata.indexed_materials,
            "learning_goal_count": metadata.learning_goal_count,
            "last_indexed_at": metadata.last_indexed_at,
        }
    )


def learning_goal_to_model(record: LearningGoalRecord) -> "LearningGoalModel":
    """Convert a parsed goal while retaining its source reference."""
    from .subjects import LearningGoalModel

    return LearningGoalModel(
        learning_goal_id=record.learning_goal_id,
        subject_id=record.subject_id,
        component_subject_id=record.component_subject_id,
        title=record.title,
        text=record.text,
        order=record.order,
        source=MaterialSourceModel(
            source_id=record.learning_goal_id,
            source_name=record.source_name,
            source_layer=record.source_layer,
        ),
    )


def material_inventory_to_model(item: MaterialInventoryItem) -> MaterialModel:
    """Convert backend file metadata without exposing an absolute path."""
    return MaterialModel(
        material_id=item.material_id,
        subject_id=item.subject_id,
        component_subject_id=item.component_subject_id,
        material_name=item.material_name,
        file_name=item.file_name,
        media_type=item.media_type,
        section=item.section,
        archived=item.archived,
        status=item.status,
        size_bytes=item.size_bytes,
        chunks_indexed=item.chunks_indexed,
        created_at=item.created_at,
        indexed_at=item.indexed_at,
        warning=item.warning,
        sources=[
            MaterialSourceModel(
                source_id=item.material_id,
                source_name=item.file_name,
                source_layer=item.source_layer,
            )
        ],
    )


def document_import_to_response(result: DocumentImportResult) -> DocumentImportResponse:
    """Convert a safe upload result to the exact multipart response contract."""
    return DocumentImportResponse(
        material_id=result.material_id,
        name=result.name,
        type=result.media_type,
        section=result.section,
        language=result.language,
        pages=result.pages,
        chunks_indexed=result.chunks_indexed,
        status=result.status,
        warnings=list(result.warnings),
        added_at=result.added_at,
    )


def _stable_source_id(source: RetrievedChunk) -> str:
    metadata = source.metadata
    explicit = metadata.get("source_id") or metadata.get("chunk_id")
    if explicit:
        return str(explicit)
    seed = "|".join(
        [
            str(metadata.get("source_name", "source")),
            str(metadata.get("page_number", "")),
            source.text[:200],
        ]
    )
    return "src_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def source_snippet_from_chunk(source: RetrievedChunk, *, max_snippet_chars: int = 1200) -> SourceSnippet:
    """Map real chunk metadata without inventing missing page or URL values."""
    metadata = source.metadata
    material_id = metadata.get("material_id") or metadata.get("source_id")
    page = metadata.get("page_number")
    return SourceSnippet(
        source_id=_stable_source_id(source),
        material_id=str(material_id) if material_id else None,
        material_name=str(metadata.get("original_name") or metadata.get("source_name", "source")),
        section=str(metadata["section"]) if metadata.get("section") else None,
        page=int(page) if page not in {None, ""} else None,
        snippet=source.text[:max_snippet_chars],
        score=float(source.score),
        url=str(metadata["url"]) if metadata.get("url") else None,
    )


def api_chat_to_response(
    result: ApiChatResult,
    *,
    thread_id: str,
    language: str,
    include_sources: bool,
) -> ChatResponse:
    """Convert an API chat result without inventing evidence metadata."""
    return ChatResponse(
        thread_id=thread_id,
        message_id=result.message_id,
        answer=result.answer,
        sources=(
            [source_snippet_from_chunk(source) for source in result.sources]
            if include_sources
            else []
        ),
        exam_tip=result.exam_tip,
        used_model=result.used_model,
        retrieval_summary=RetrievalSummary(
            chunks_considered=result.chunks_considered,
            chunks_used=len(result.sources),
            collection_names=list(result.collection_names),
            material_ids=list(result.material_ids),
            learning_goal_id=result.learning_goal_id,
        ),
        language=language,
        created_at=result.created_at,
    )


def api_chat_done_payload(result: ApiChatResult, *, include_sources: bool) -> dict:
    """Build the exact final SSE metadata object without repeating answer text."""
    return {
        "message_id": result.message_id,
        "sources": (
            [
                source_snippet_from_chunk(source).model_dump(mode="json")
                for source in result.sources
            ]
            if include_sources
            else []
        ),
        "exam_tip": result.exam_tip,
        "used_model": result.used_model,
        "retrieval_summary": {
            "chunks_considered": result.chunks_considered,
            "chunks_used": len(result.sources),
            "collection_names": list(result.collection_names),
            "material_ids": list(result.material_ids),
            "learning_goal_id": result.learning_goal_id,
        },
        "created_at": result.created_at.isoformat().replace("+00:00", "Z"),
    }


def quiz_to_response(
    result: QuizApiResult, *, subject_id: str, component_subject_id: str | None, language: str
) -> Quiz:
    """Map visible quiz questions while keeping persisted solutions hidden."""
    return Quiz(
        quiz_id=result.quiz_id,
        subject_id=subject_id,
        component_subject_id=component_subject_id,
        language=language,
        title=result.title,
        difficulty=result.difficulty,
        questions=[
            QuizQuestion(
                question_id=item.question_id,
                question_type=item.question_type,
                prompt=item.prompt,
                options=list(item.options),
                points=item.points,
                learning_goal_id=item.learning_goal_id,
                correct_index=None,
                expected_answer=None,
                correct_answer=None,
                explanation=None,
            )
            for item in result.questions
        ],
        sources=[source_snippet_from_chunk(source) for source in result.sources],
        used_model=result.used_model,
        created_at=result.created_at,
    )


def mock_exam_to_response(
    result: MockExamApiResult,
    *,
    subject_id: str,
    component_subject_id: str | None,
    language: str,
) -> MockExam:
    """Map a mock exam without exposing protected model answers."""
    return MockExam(
        mock_exam_id=result.mock_exam_id,
        subject_id=subject_id,
        component_subject_id=component_subject_id,
        language=language,
        title=result.title,
        difficulty=result.difficulty,
        total_points=result.total_points,
        questions=[
            MockExamQuestion(
                question_id=item.question_id,
                question_type=item.question_type,
                prompt=item.prompt,
                points=item.points,
                options=list(item.options),
                learning_goal_id=item.learning_goal_id,
                marking_criteria=list(item.marking_criteria),
                model_answer=None,
            )
            for item in result.questions
        ],
        sources=[source_snippet_from_chunk(source) for source in result.sources],
        used_model=result.used_model,
        created_at=result.created_at,
    )


def study_plan_to_response(
    result: StudyPlanApiResult,
    *,
    subject_id: str,
    component_subject_id: str | None,
    language: str,
) -> StudyPlan:
    """Map a proposal without writing frontend planner events."""
    return StudyPlan(
        study_plan_id=result.study_plan_id,
        subject_id=subject_id,
        component_subject_id=component_subject_id,
        language=language,
        exam_date=result.exam_date,
        items=[StudyPlanItem(**item.__dict__) for item in result.items],
        summary=result.summary,
        sources=[source_snippet_from_chunk(source) for source in result.sources],
        used_model=result.used_model,
        created_at=result.created_at,
    )


def grading_api_to_response(result: GradingApiResult) -> GradingResult:
    """Apply the exact unrounded Swiss formula to grounded model-awarded points."""
    return GradingResult(
        points_awarded=result.points_awarded,
        max_points=result.max_points,
        swiss_grade=max(1.0, min(6.0, 1 + 5 * result.points_awarded / result.max_points)),
        grade_formula="points_awarded / max_points * 5 + 1",
        strengths=list(result.strengths),
        missing_points=list(result.missing_points),
        improvement_advice=list(result.improvement_advice),
        rubric_used=list(result.rubric_used),
        sources=[source_snippet_from_chunk(source) for source in result.sources],
        graded_at=result.graded_at,
        used_model=result.used_model,
    )


def model_status_to_schema(status: ModelStatusSnapshot) -> ModelStatus:
    """Convert provider status to its Pydantic wire model."""
    return ModelStatus.model_validate(asdict(status))


def backend_health_to_schema(status: ApiHealthSnapshot) -> BackendHealth:
    """Convert combined health status to its Pydantic wire model."""
    return BackendHealth.model_validate(asdict(status))


def grading_result_from_points(
    *,
    points_awarded: float,
    max_points: float,
    strengths: list[str] | None = None,
    missing_points: list[str] | None = None,
    improvement_advice: list[str] | None = None,
    rubric_used: list[str] | None = None,
    sources: list[SourceSnippet] | None = None,
    used_model: str,
) -> GradingResult:
    """Build an exact, clamped Swiss-grade result without display rounding."""
    if max_points <= 0:
        raise ValueError("max_points must be positive")
    if points_awarded < 0 or points_awarded > max_points:
        raise ValueError("points_awarded must be between 0 and max_points")
    swiss_grade = max(1.0, min(6.0, points_awarded / max_points * 5.0 + 1.0))
    return GradingResult(
        points_awarded=points_awarded,
        max_points=max_points,
        swiss_grade=swiss_grade,
        grade_formula="points_awarded / max_points * 5 + 1",
        strengths=strengths or [],
        missing_points=missing_points or [],
        improvement_advice=improvement_advice or [],
        rubric_used=rubric_used or [],
        sources=sources or [],
        graded_at=utc_now(),
        used_model=used_model,
    )
