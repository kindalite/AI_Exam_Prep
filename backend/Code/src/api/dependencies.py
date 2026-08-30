"""Reusable FastAPI dependencies for config, identity, services, and request ID."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Callable

from fastapi import Depends, Header, Request

from ..config import AppConfig, load_config
from ..services.health_service import get_api_health, get_model_status_snapshot
from ..services.chat_service import finalize_api_chat, open_api_chat_stream, prepare_api_chat, run_api_chat
from ..services.identity_service import StudentContext, resolve_student_context
from ..services.material_service import material_inventory
from ..services.grading_service import generate_grading_api
from ..services.feedback_service import submit_api_feedback
from ..services.mock_exam_service import generate_mock_exam_api
from ..services.quiz_service import generate_quiz_api
from ..services.study_plan_service import generate_study_plan_api
from ..services.subject_service import list_learning_goals, subject_read_metadata
from ..services.upload_service import import_student_document
from .errors import ApiDomainError


@dataclass(frozen=True)
class ApiServices:
    """Injectable service callables used by thin route adapters."""

    health: Callable = get_api_health
    model_status: Callable = get_model_status_snapshot
    subject_metadata: Callable = subject_read_metadata
    learning_goals: Callable = list_learning_goals
    materials: Callable = material_inventory
    import_document: Callable = import_student_document
    chat: Callable = run_api_chat
    prepare_chat: Callable = prepare_api_chat
    open_chat_stream: Callable = open_api_chat_stream
    finalize_chat: Callable = finalize_api_chat
    generate_quiz: Callable = generate_quiz_api
    generate_mock_exam: Callable = generate_mock_exam_api
    generate_study_plan: Callable = generate_study_plan_api
    grade: Callable = generate_grading_api
    feedback: Callable = submit_api_feedback


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Return immutable application config; tests may override this dependency."""
    return load_config()


def get_api_services() -> ApiServices:
    """Return stateless framework-neutral service callables."""
    return ApiServices()


def get_request_id(request: Request) -> str:
    """Return the request ID assigned by middleware."""
    return str(request.state.request_id)


def get_student_context(
    x_student_id: str | None = Header(default=None, alias="X-Student-Id"),
    config: AppConfig = Depends(get_config),
) -> StudentContext:
    """Resolve required Stage-1 student identity for user-scoped routes."""
    try:
        return resolve_student_context(
            x_student_id,
            fallback_student_id=config.api_dev_student_id or None,
        )
    except ValueError as exc:
        raise ApiDomainError(
            code="student_identity_required",
            message="X-Student-Id is required for this operation.",
            detail=str(exc),
            retryable=False,
            status_code=401,
        ) from exc


def get_optional_student_context(
    x_student_id: str | None = Header(default=None, alias="X-Student-Id"),
    config: AppConfig = Depends(get_config),
) -> StudentContext | None:
    """Resolve identity when supplied; otherwise select canonical shared-only mode."""
    if not x_student_id and not config.api_dev_student_id:
        return None
    try:
        return resolve_student_context(
            x_student_id,
            fallback_student_id=config.api_dev_student_id or None,
        )
    except ValueError as exc:
        raise ApiDomainError(
            code="student_identity_invalid",
            message="X-Student-Id is invalid.",
            detail=str(exc),
            retryable=False,
            status_code=400,
        ) from exc
