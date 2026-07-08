"""Practice grading helpers using the Swiss point-based formula."""

from __future__ import annotations

from dataclasses import dataclass

from .llm_client import LLMResponse, generate_response
from .prompts import build_grading_prompt, build_system_prompt
from .retrieval import load_exam_criteria, retrieve_for_subject
from .subject_registry import Subject


@dataclass(frozen=True)
class GradeResult:
    """Point and grade result for practice feedback."""

    points_achieved: float
    maximum_points: float
    grade: float


def calculate_grade(points_achieved: float, maximum_points: float) -> GradeResult:
    """Calculate the Swiss grade formula and validate point values."""
    if maximum_points <= 0:
        raise ValueError("maximum_points must be positive")
    if points_achieved < 0 or points_achieved > maximum_points:
        raise ValueError("points_achieved must be between 0 and maximum_points")
    grade = (points_achieved / maximum_points) * 5 + 1
    return GradeResult(points_achieved, maximum_points, round(grade, 2))


def create_grading_feedback(
    subject: Subject,
    language: str,
    question: str,
    student_answer: str,
    maximum_points: float,
    marking_scheme: str = "",
    call_llm: bool = True,
) -> LLMResponse:
    """Prepare practice grading feedback with the local LLM."""
    if maximum_points <= 0:
        return LLMResponse("", False, "Maximum points must be positive.")
    retrieved = retrieve_for_subject(subject, question)
    criteria = load_exam_criteria(subject)
    prompt = build_grading_prompt(subject, language, question, student_answer, maximum_points, marking_scheme, retrieved.context, criteria)
    if not call_llm:
        return LLMResponse(prompt, True)
    return generate_response(prompt, build_system_prompt(subject, language))

