"""Subject catalogue, detail, learning-goal, and material read routes."""

from fastapi import APIRouter, Depends, Query

from ...config import AppConfig
from ...services.identity_service import StudentContext
from ...subject_registry import get_subject, subjects_for_display, validate_component_for_subject, validate_top_level_subject_id
from ..dependencies import ApiServices, get_api_services, get_config, get_optional_student_context
from ..errors import ApiDomainError
from ..schemas.adapters import learning_goal_to_model, material_inventory_to_model, subject_with_metadata_to_model
from ..schemas.materials import MaterialModel
from ..schemas.subjects import LearningGoalModel, SubjectModel

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


def _validated_scope(subject_id: str, component_subject_id: str | None) -> tuple[str, str | None]:
    """Map path/query validation failures to stable API error codes."""
    try:
        normalized = validate_top_level_subject_id(subject_id)
    except ValueError as exc:
        raise ApiDomainError(
            code="subject_not_found",
            message=f"Unknown subject_id: {subject_id}",
            detail=str(exc),
            status_code=404,
        ) from exc
    try:
        component = validate_component_for_subject(normalized, component_subject_id)
    except ValueError as exc:
        raise ApiDomainError(
            code="invalid_subject_component",
            message="component_subject_id is invalid for this subject.",
            detail=str(exc),
            status_code=422,
        ) from exc
    return normalized, component


@router.get("", response_model=list[SubjectModel])
def list_subject_catalog(
    config: AppConfig = Depends(get_config),
    student: StudentContext | None = Depends(get_optional_student_context),
    services: ApiServices = Depends(get_api_services),
) -> list[SubjectModel]:
    """Return exactly 15 top-level subjects; omit private metadata when anonymous."""
    student_id = student.student_id if student else None
    return [
        subject_with_metadata_to_model(
            subject,
            services.subject_metadata(config, subject.key, student_id=student_id),
            config=config,
        )
        for subject in subjects_for_display(config)
    ]


@router.get("/{subject_id}", response_model=SubjectModel)
def get_subject_detail(
    subject_id: str,
    component_subject_id: str | None = Query(default=None),
    config: AppConfig = Depends(get_config),
    student: StudentContext | None = Depends(get_optional_student_context),
    services: ApiServices = Depends(get_api_services),
) -> SubjectModel:
    """Return aggregate or component-specific corpus metadata."""
    normalized, component = _validated_scope(subject_id, component_subject_id)
    metadata = services.subject_metadata(
        config,
        normalized,
        component_subject_id=component,
        student_id=student.student_id if student else None,
    )
    return subject_with_metadata_to_model(get_subject(normalized, config), metadata, config=config)


@router.get("/{subject_id}/learning-goals", response_model=list[LearningGoalModel])
def get_learning_goals(
    subject_id: str,
    component_subject_id: str | None = Query(default=None),
    topic: str | None = Query(default=None, max_length=200),
    config: AppConfig = Depends(get_config),
    student: StudentContext | None = Depends(get_optional_student_context),
    services: ApiServices = Depends(get_api_services),
) -> list[LearningGoalModel]:
    """Return user-specific goals when identified, otherwise canonical goals."""
    normalized, component = _validated_scope(subject_id, component_subject_id)
    records = services.learning_goals(
        config,
        normalized,
        component_subject_id=component,
        student_id=student.student_id if student else None,
        topic=topic,
    )
    return [learning_goal_to_model(record) for record in records]


@router.get("/{subject_id}/materials", response_model=list[MaterialModel])
def get_materials(
    subject_id: str,
    component_subject_id: str | None = Query(default=None),
    section: str | None = Query(default=None, max_length=200),
    include_archived: bool = Query(default=False),
    config: AppConfig = Depends(get_config),
    student: StudentContext | None = Depends(get_optional_student_context),
    services: ApiServices = Depends(get_api_services),
) -> list[MaterialModel]:
    """Return canonical-only material anonymously or isolated user material with identity."""
    normalized, component = _validated_scope(subject_id, component_subject_id)
    items = services.materials(
        config,
        normalized,
        component_subject_id=component,
        student_id=student.student_id if student else None,
        section=section,
        include_archived=include_archived,
    )
    return [material_inventory_to_model(item) for item in items]
