"""Framework-neutral mock-exam generation and timed-attempt orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Callable

from ..adaptive_learning import choose_adaptive_difficulty
from ..config import AppConfig
from ..exam_mode import generate_exam_set, start_exam_mode
from ..llm_client import LLMResponse, generate_response
from ..practice_store import new_generated_practice, new_solution_set, save_generated_exam, save_solution_set
from ..prompts import build_mock_exam_prompt, build_system_prompt
from ..retrieval import sources_to_context
from ..subject_languages import language_name
from ..subject_registry import Subject, corpus_keys_for_request, get_subject
from ..vector_store import RetrievedChunk
from .chat_service import learning_goal_context, read_scoped_file, retrieve_scoped_evidence
from .identity_service import StudentContext
from .structured_output import call_structured_model


def generate_mock_exam(
    subject: Subject,
    language: str,
    total_points: int,
    difficulty: str,
    *,
    call_llm: bool = True,
) -> LLMResponse:
    """Generate a mock exam through the existing implementation."""
    return generate_exam_set(subject, language, total_points, difficulty, call_llm=call_llm)


def start_timed_mock_exam(
    *,
    user_id: str,
    subject: Subject,
    language: str,
    topic: str,
    difficulty_requested: str,
    timer_minutes: int,
    generated_text: str,
    config: AppConfig,
):
    """Persist a generated mock exam and start its timed session."""
    used = (
        choose_adaptive_difficulty(subject.key, topic, config)
        if difficulty_requested == "adaptive"
        else difficulty_requested
    )
    return start_exam_mode(
        user_id,
        subject,
        language,
        topic,
        difficulty_requested,
        used,
        timer_minutes,
        generated_text,
        config,
    )


@dataclass(frozen=True)
class MockExamQuestionResult:
    """Visible mock-exam question; model answers remain protected in storage."""

    question_id: str
    question_type: str
    prompt: str
    points: float
    options: tuple[str, ...]
    learning_goal_id: str | None
    marking_criteria: tuple[str, ...]


@dataclass(frozen=True)
class MockExamApiResult:
    """Structured persisted mock exam for the API adapter."""

    mock_exam_id: str
    title: str
    difficulty: str
    total_points: float
    questions: tuple[MockExamQuestionResult, ...]
    sources: tuple[RetrievedChunk, ...]
    used_model: str
    created_at: datetime


def _validate_exam_payload(value: dict, total_points: float) -> tuple[str, list[dict]]:
    title = str(value.get("title", "")).strip()
    raw_questions = value.get("questions")
    if not title or not isinstance(raw_questions, list) or not raw_questions:
        raise ValueError("A title and at least one question are required")
    allowed = {"multiple_choice", "short_answer", "long_answer", "true_false"}
    rows: list[dict] = []
    for index, raw in enumerate(raw_questions, start=1):
        if not isinstance(raw, dict):
            raise ValueError("Every question must be an object")
        question_type = str(raw.get("question_type", ""))
        prompt = str(raw.get("prompt", "")).strip()
        points = float(raw.get("points", 0))
        criteria = raw.get("marking_criteria") or []
        if question_type not in allowed or not prompt or points <= 0 or not isinstance(criteria, list):
            raise ValueError(f"Question {index} is malformed")
        rows.append(
            {
                "question_id": f"q{index}",
                "question_type": question_type,
                "prompt": prompt,
                "points": points,
                "options": [str(item) for item in (raw.get("options") or [])],
                "marking_criteria": [str(item) for item in criteria if str(item).strip()],
                "model_answer": str(raw.get("model_answer", "")).strip() or None,
            }
        )
    generated_total = sum(row["points"] for row in rows)
    if generated_total <= 0:
        raise ValueError("Question points must have a positive total")
    scale = total_points / generated_total
    allocated = 0.0
    for row in rows[:-1]:
        row["points"] = round(row["points"] * scale, 4)
        allocated += row["points"]
    rows[-1]["points"] = round(total_points - allocated, 4)
    if rows[-1]["points"] <= 0:
        raise ValueError("Normalized final question points are not positive")
    return title, rows


def generate_mock_exam_api(
    *,
    subject_id: str,
    component_subject_id: str | None,
    language: str,
    total_points: float,
    difficulty: str,
    topics: list[str],
    learning_goal_ids: list[str],
    material_ids: list[str],
    student: StudentContext,
    config: AppConfig,
    vector_store=None,
    call_llm: Callable[..., LLMResponse] = generate_response,
) -> MockExamApiResult:
    """Generate, normalize, protect solutions, and persist a user-scoped mock exam."""
    subject = get_subject(subject_id, config)
    corpus_keys = corpus_keys_for_request(subject_id, component_subject_id)
    goal_sections = [
        learning_goal_context(
            config=config,
            student_id=student.student_id,
            subject_id=subject_id,
            component_subject_id=component_subject_id,
            learning_goal_id=goal_id,
        )
        for goal_id in learning_goal_ids
    ] or [
        learning_goal_context(
            config=config,
            student_id=student.student_id,
            subject_id=subject_id,
            component_subject_id=component_subject_id,
            learning_goal_id=None,
        )
    ]
    goal_text = "\n".join(goal_sections)
    query = " ".join(topics) or goal_text or "mock exam"
    scoped = retrieve_scoped_evidence(
        subject_id=subject_id,
        component_subject_id=component_subject_id,
        question=query,
        material_ids=material_ids,
        top_k=10,
        student=student,
        config=config,
        vector_store=vector_store,
    )
    criteria = read_scoped_file(student.student_id, corpus_keys, config, "exam_criteria.md")
    difficulty_used = "medium" if difficulty == "adaptive" else difficulty
    prompt = build_mock_exam_prompt(
        subject,
        language_name(language),
        int(total_points),
        difficulty_used,
        sources_to_context(list(scoped.sources)),
        criteria,
        goal_text,
        sources_to_context(list(scoped.memory_sources)),
    )
    prompt += (
        "\n\nReturn exactly one JSON object with title and questions. Every question must have "
        "question_type, prompt, points, options, marking_criteria, and model_answer. No Markdown."
    )
    title, raw_questions = call_structured_model(
        prompt=prompt,
        system_prompt=build_system_prompt(subject, language),
        config=config,
        call_llm=call_llm,
        validate=lambda value: _validate_exam_payload(value, total_points),
    )
    visible = tuple(
        MockExamQuestionResult(
            question_id=row["question_id"],
            question_type=row["question_type"],
            prompt=row["prompt"],
            points=row["points"],
            options=tuple(row["options"]),
            learning_goal_id=learning_goal_ids[0] if len(learning_goal_ids) == 1 else None,
            marking_criteria=tuple(row["marking_criteria"]),
        )
        for row in raw_questions
    )
    practice = new_generated_practice(
        user_id=student.student_id,
        subject_key=component_subject_id or subject_id,
        mode="exam",
        language=language,
        topic=", ".join(topics),
        learning_goal=learning_goal_ids[0] if len(learning_goal_ids) == 1 else None,
        difficulty_requested=difficulty,
        difficulty_used=difficulty_used,
        timer_seconds=0,
        question_set=json.dumps([question.__dict__ for question in visible], ensure_ascii=False),
        solution_set_path="",
        sources=[dict(source.metadata) for source in scoped.sources],
    )
    solution = new_solution_set(
        user_id=student.student_id,
        subject_key=component_subject_id or subject_id,
        mode="exam",
        practice_id=practice.practice_id,
        solution_set=json.dumps(raw_questions, ensure_ascii=False),
    )
    solution_row = save_solution_set(solution, config)
    practice = replace(practice, solution_set_path=solution_row["path"])
    save_generated_exam(practice, config)
    return MockExamApiResult(
        mock_exam_id=practice.practice_id,
        title=title,
        difficulty=difficulty_used,
        total_points=total_points,
        questions=visible,
        sources=scoped.sources,
        used_model=config.generation_model,
        created_at=datetime.now(timezone.utc),
    )
