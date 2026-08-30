"""Structured user-scoped quiz, exam, plan, and grading routes."""

from __future__ import annotations

import asyncio
from functools import partial

import anyio
from fastapi import APIRouter, Depends

from ...config import AppConfig
from ...services.chat_service import ChatLearningGoalError
from ...services.identity_service import StudentContext
from ...services.structured_output import InvalidStructuredOutputError, StructuredModelUnavailableError
from ..dependencies import ApiServices, get_api_services, get_config, get_student_context
from ..errors import ApiDomainError
from ..schemas.adapters import grading_api_to_response, mock_exam_to_response, quiz_to_response, study_plan_to_response
from ..schemas.grading import GradingRequest, GradingResult
from ..schemas.mock_exam import MockExam, MockExamRequest
from ..schemas.quiz import Quiz, QuizRequest
from ..schemas.study_plan import StudyPlan, StudyPlanRequest

router = APIRouter(prefix="/api", tags=["study_tools"])


async def _run(operation, config: AppConfig):
    """Run synchronous local inference off-loop with a bounded request lifetime."""
    try:
        return await asyncio.wait_for(
            anyio.to_thread.run_sync(operation, abandon_on_cancel=True),
            timeout=config.api_generation_timeout_seconds,
        )
    except TimeoutError as exc:
        raise ApiDomainError(
            "generation_timeout",
            "The AI operation exceeded its local timeout.",
            f"Timeout after {config.api_generation_timeout_seconds} seconds.",
            True,
            504,
        ) from exc
    except StructuredModelUnavailableError as exc:
        raise ApiDomainError("model_unavailable", "The local model is unavailable.", str(exc), True, 503) from exc
    except InvalidStructuredOutputError as exc:
        raise ApiDomainError("invalid_model_output", "The model returned malformed structured output.", str(exc), True, 502) from exc
    except ChatLearningGoalError as exc:
        raise ApiDomainError("invalid_learning_goal", "A learning goal is outside this subject scope.", str(exc), False, 422) from exc
    except ValueError as exc:
        raise ApiDomainError("validation_error", "The generation request is invalid.", str(exc), False, 422) from exc


@router.post("/quiz/generate", response_model=Quiz)
async def generate_quiz(
    payload: QuizRequest,
    student: StudentContext = Depends(get_student_context),
    config: AppConfig = Depends(get_config),
    services: ApiServices = Depends(get_api_services),
) -> Quiz:
    result = await _run(partial(services.generate_quiz, **payload.model_dump(exclude={"academic_year", "grade_level"}), student=student, config=config), config)
    return quiz_to_response(result, subject_id=payload.subject_id, component_subject_id=payload.component_subject_id, language=payload.language)


@router.post("/mock-exam/generate", response_model=MockExam)
async def generate_mock_exam(
    payload: MockExamRequest,
    student: StudentContext = Depends(get_student_context),
    config: AppConfig = Depends(get_config),
    services: ApiServices = Depends(get_api_services),
) -> MockExam:
    result = await _run(partial(services.generate_mock_exam, **payload.model_dump(exclude={"academic_year", "grade_level"}), student=student, config=config), config)
    return mock_exam_to_response(result, subject_id=payload.subject_id, component_subject_id=payload.component_subject_id, language=payload.language)


@router.post("/study-plan/generate", response_model=StudyPlan)
async def generate_study_plan(
    payload: StudyPlanRequest,
    student: StudentContext = Depends(get_student_context),
    config: AppConfig = Depends(get_config),
    services: ApiServices = Depends(get_api_services),
) -> StudyPlan:
    result = await _run(partial(services.generate_study_plan, **payload.model_dump(exclude={"academic_year", "grade_level"}), student=student, config=config), config)
    return study_plan_to_response(result, subject_id=payload.subject_id, component_subject_id=payload.component_subject_id, language=payload.language)


@router.post("/grade", response_model=GradingResult)
async def grade(
    payload: GradingRequest,
    student: StudentContext = Depends(get_student_context),
    config: AppConfig = Depends(get_config),
    services: ApiServices = Depends(get_api_services),
) -> GradingResult:
    values = payload.model_dump(exclude={"academic_year", "grade_level"})
    values["marking_scheme"] = values.get("marking_scheme") or ""
    result = await _run(partial(services.grade, **values, student=student, config=config), config)
    return grading_api_to_response(result)
