"""Framework-neutral grading calculation, feedback, and persistence services."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from ..config import AppConfig
from ..grader import GradeResult, calculate_grade, create_grading_feedback, store_grading_attempt
from ..llm_client import LLMResponse, generate_response
from ..practice_store import new_performance_report, save_performance_report
from ..prompts import build_grading_prompt, build_system_prompt
from ..retrieval import sources_to_context
from ..subject_languages import language_name
from ..subject_registry import Subject, corpus_keys_for_request, get_subject
from ..vector_store import RetrievedChunk
from .chat_service import read_scoped_file, retrieve_scoped_evidence
from .identity_service import StudentContext
from .structured_output import call_structured_model


def calculate_swiss_grade(points_achieved: float, maximum_points: float) -> GradeResult:
    """Calculate the existing validated Swiss formula result."""
    return calculate_grade(points_achieved, maximum_points)


def generate_grading_feedback(
    subject: Subject,
    language: str,
    question: str,
    student_answer: str,
    maximum_points: float,
    marking_scheme: str = "",
    *,
    call_llm: bool = True,
) -> LLMResponse:
    """Generate AI practice feedback through the existing grader."""
    return create_grading_feedback(
        subject,
        language,
        question,
        student_answer,
        maximum_points,
        marking_scheme,
        call_llm=call_llm,
    )


def save_grading_attempt(
    subject: Subject,
    question: str,
    student_answer: str,
    feedback: str,
    points: float,
    maximum_points: float,
    config: AppConfig,
) -> dict:
    """Persist one manual grading attempt through the existing store."""
    return store_grading_attempt(
        subject,
        question,
        student_answer,
        feedback,
        points,
        maximum_points,
        config,
    )


@dataclass(frozen=True)
class GradingApiResult:
    """Structured exact API grading result before schema adaptation."""

    points_awarded: float
    max_points: float
    strengths: tuple[str, ...]
    missing_points: tuple[str, ...]
    improvement_advice: tuple[str, ...]
    rubric_used: tuple[str, ...]
    sources: tuple[RetrievedChunk, ...]
    used_model: str
    graded_at: datetime


def _list_field(value: dict, key: str) -> tuple[str, ...]:
    raw = value.get(key) or []
    if not isinstance(raw, list):
        raise ValueError(f"{key} must be a list")
    return tuple(str(item).strip() for item in raw if str(item).strip())


def _validate_grading_payload(value: dict, max_points: float) -> dict:
    points = float(value.get("points_awarded"))
    if points < 0 or points > max_points:
        raise ValueError("points_awarded must be between zero and max_points")
    return {
        "points_awarded": points,
        "strengths": _list_field(value, "strengths"),
        "missing_points": _list_field(value, "missing_points"),
        "improvement_advice": _list_field(value, "improvement_advice"),
    }


def _rubric_lines(marking_scheme: str, criteria: str) -> tuple[str, ...]:
    """Return only rubric lines that came from the request or stored criteria."""
    lines: list[str] = []
    for block in (marking_scheme, criteria):
        for raw in block.splitlines():
            line = raw.strip().lstrip("-*# ").strip()
            if line and not line.lower().startswith(("exam criteria", "add ")):
                lines.append(line)
    return tuple(dict.fromkeys(lines))


def generate_grading_api(
    *,
    subject_id: str,
    component_subject_id: str | None,
    language: str,
    question: str,
    student_answer: str,
    max_points: float,
    marking_scheme: str,
    material_ids: list[str],
    student: StudentContext,
    config: AppConfig,
    vector_store=None,
    call_llm: Callable[..., LLMResponse] = generate_response,
) -> GradingApiResult:
    """Grade one practice answer from user-scoped evidence and grounded criteria."""
    subject = get_subject(subject_id, config)
    corpus_keys = corpus_keys_for_request(subject_id, component_subject_id)
    scoped = retrieve_scoped_evidence(
        subject_id=subject_id,
        component_subject_id=component_subject_id,
        question=question,
        material_ids=material_ids,
        top_k=8,
        student=student,
        config=config,
        vector_store=vector_store,
    )
    criteria = read_scoped_file(student.student_id, corpus_keys, config, "exam_criteria.md")
    allowed_rubric = _rubric_lines(marking_scheme, criteria)
    prompt = build_grading_prompt(
        subject,
        language_name(language),
        question,
        student_answer,
        max_points,
        marking_scheme,
        sources_to_context(list(scoped.sources)),
        criteria,
    )
    prompt += (
        "\n\nReturn exactly one JSON object with points_awarded, strengths, missing_points, "
        "and improvement_advice. The last three fields are arrays of strings. Do not invent "
        "rubric criteria and do not return a rounded grade. No Markdown."
    )
    parsed = call_structured_model(
        prompt=prompt,
        system_prompt=build_system_prompt(subject, language),
        config=config,
        call_llm=call_llm,
        validate=lambda value: _validate_grading_payload(value, max_points),
    )
    graded_at = datetime.now(timezone.utc)
    exact_grade = max(1.0, min(6.0, 1.0 + 5.0 * parsed["points_awarded"] / max_points))
    practice_id = "grade_" + hashlib.sha256(
        f"{student.student_id}|{subject_id}|{question}|{graded_at.isoformat()}".encode("utf-8")
    ).hexdigest()[:20]
    save_performance_report(
        new_performance_report(
            user_id=student.student_id,
            subject_key=component_subject_id or subject_id,
            practice_id=practice_id,
            points_achieved=parsed["points_awarded"],
            maximum_points=max_points,
            grade=exact_grade,
            strengths=list(parsed["strengths"]),
            weaknesses=list(parsed["missing_points"]),
            recommended_actions=list(parsed["improvement_advice"]),
            source_layers_used=list(
                dict.fromkeys(str(source.metadata.get("source_layer", "")) for source in scoped.sources)
            ),
        ),
        config,
    )
    return GradingApiResult(
        points_awarded=parsed["points_awarded"],
        max_points=max_points,
        strengths=parsed["strengths"],
        missing_points=parsed["missing_points"],
        improvement_advice=parsed["improvement_advice"],
        rubric_used=allowed_rubric,
        sources=scoped.sources,
        used_model=config.generation_model,
        graded_at=graded_at,
    )
