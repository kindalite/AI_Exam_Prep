"""Framework-neutral quiz generation and timed-attempt orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Callable

from ..adaptive_learning import choose_adaptive_difficulty
from ..config import AppConfig
from ..llm_client import LLMResponse, generate_response
from ..practice_store import new_generated_practice, new_solution_set, save_generated_quiz, save_solution_set
from ..prompts import build_quiz_prompt, build_system_prompt
from ..quiz_mode import generate_quiz_set, start_quiz_mode
from ..retrieval import sources_to_context
from ..subject_languages import language_name
from ..subject_registry import Subject, corpus_keys_for_request, get_subject
from ..vector_store import RetrievedChunk
from .chat_service import learning_goal_context, read_scoped_file, retrieve_scoped_evidence
from .identity_service import StudentContext
from .structured_output import call_structured_model


def generate_quiz(
    subject: Subject,
    language: str,
    learning_goal: str,
    difficulty: str,
    *,
    number_of_questions: int | None = None,
    call_llm: bool = True,
) -> LLMResponse:
    """Generate a quiz through the existing generator implementation."""
    if number_of_questions is None:
        from ..quiz_generator import create_quiz

        return create_quiz(subject, language, learning_goal, difficulty, call_llm=call_llm)
    return generate_quiz_set(
        subject,
        language,
        learning_goal,
        difficulty,
        number_of_questions,
        call_llm=call_llm,
    )


def start_timed_quiz(
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
    """Persist a generated quiz and start its timed session."""
    used = (
        choose_adaptive_difficulty(subject.key, topic, config)
        if difficulty_requested == "adaptive"
        else difficulty_requested
    )
    return start_quiz_mode(
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
class QuizQuestionResult:
    """Visible quiz question plus separately retained hidden solution fields."""

    question_id: str
    question_type: str
    prompt: str
    options: tuple[str, ...]
    points: float
    learning_goal_id: str | None
    correct_index: int | None = None
    expected_answer: str | None = None
    explanation: str | None = None


@dataclass(frozen=True)
class QuizApiResult:
    """Structured persisted quiz result for the HTTP adapter."""

    quiz_id: str
    title: str
    difficulty: str
    questions: tuple[QuizQuestionResult, ...]
    sources: tuple[RetrievedChunk, ...]
    used_model: str
    created_at: datetime


def _validate_quiz_payload(value: dict, question_count: int) -> tuple[str, list[dict]]:
    title = str(value.get("title", "")).strip()
    questions = value.get("questions")
    if not title or not isinstance(questions, list) or len(questions) != question_count:
        raise ValueError(f"Expected a title and exactly {question_count} questions")
    allowed = {"multiple_choice", "short_answer", "long_answer", "true_false"}
    normalized: list[dict] = []
    for index, raw in enumerate(questions, start=1):
        if not isinstance(raw, dict):
            raise ValueError("Every question must be an object")
        question_type = str(raw.get("question_type", ""))
        prompt = str(raw.get("prompt", "")).strip()
        options = raw.get("options") or []
        points = float(raw.get("points", 1))
        if question_type not in allowed or not prompt or points <= 0 or not isinstance(options, list):
            raise ValueError(f"Question {index} has invalid type, prompt, options, or points")
        correct_index = raw.get("correct_index")
        if correct_index is not None:
            correct_index = int(correct_index)
            if correct_index < 0 or correct_index >= len(options):
                raise ValueError(f"Question {index} correct_index is outside options")
        if question_type == "multiple_choice" and (len(options) < 2 or correct_index is None):
            raise ValueError(f"Question {index} requires options and correct_index")
        expected = str(raw.get("expected_answer", "")).strip() or None
        if question_type != "multiple_choice" and expected is None:
            raise ValueError(f"Question {index} requires expected_answer")
        normalized.append(
            {
                "question_id": f"q{index}",
                "question_type": question_type,
                "prompt": prompt,
                "options": [str(option) for option in options],
                "points": points,
                "correct_index": correct_index,
                "expected_answer": expected,
                "explanation": str(raw.get("explanation", "")).strip() or None,
            }
        )
    return title, normalized


def generate_quiz_api(
    *,
    subject_id: str,
    component_subject_id: str | None,
    language: str,
    learning_goal_id: str | None,
    topic: str | None,
    difficulty: str,
    question_count: int,
    material_ids: list[str],
    student: StudentContext,
    config: AppConfig,
    vector_store=None,
    call_llm: Callable[..., LLMResponse] = generate_response,
) -> QuizApiResult:
    """Generate, validate, hide solutions, and persist one user-scoped quiz."""
    subject = get_subject(subject_id, config)
    corpus_keys = corpus_keys_for_request(subject_id, component_subject_id)
    goal_text = learning_goal_context(
        config=config,
        student_id=student.student_id,
        subject_id=subject_id,
        component_subject_id=component_subject_id,
        learning_goal_id=learning_goal_id,
    )
    query = " ".join(part for part in (topic, goal_text, "quiz practice") if part)
    scoped = retrieve_scoped_evidence(
        subject_id=subject_id,
        component_subject_id=component_subject_id,
        question=query,
        material_ids=material_ids,
        top_k=8,
        student=student,
        config=config,
        vector_store=vector_store,
    )
    criteria = read_scoped_file(student.student_id, corpus_keys, config, "exam_criteria.md")
    difficulty_used = "medium" if difficulty == "adaptive" else difficulty
    prompt = build_quiz_prompt(
        subject,
        language_name(language),
        goal_text or topic or "Use the available learning goals.",
        difficulty_used,
        sources_to_context(list(scoped.sources)),
        criteria,
        sources_to_context(list(scoped.memory_sources)),
    )
    prompt += (
        f"\n\nReturn exactly one JSON object with title and exactly {question_count} questions. "
        "Each question must contain question_type, prompt, options, points, correct_index, "
        "expected_answer, and explanation. Use only these question types: multiple_choice, "
        "short_answer, long_answer, true_false. No Markdown."
    )
    title, raw_questions = call_structured_model(
        prompt=prompt,
        system_prompt=build_system_prompt(subject, language),
        config=config,
        call_llm=call_llm,
        validate=lambda value: _validate_quiz_payload(value, question_count),
    )
    visible_questions = tuple(
        QuizQuestionResult(
            question_id=row["question_id"],
            question_type=row["question_type"],
            prompt=row["prompt"],
            options=tuple(row["options"]),
            points=row["points"],
            learning_goal_id=learning_goal_id,
        )
        for row in raw_questions
    )
    practice = new_generated_practice(
        user_id=student.student_id,
        subject_key=component_subject_id or subject_id,
        mode="quiz",
        language=language,
        topic=topic or goal_text[:200],
        learning_goal=learning_goal_id,
        difficulty_requested=difficulty,
        difficulty_used=difficulty_used,
        timer_seconds=0,
        question_set=json.dumps([question.__dict__ for question in visible_questions], ensure_ascii=False),
        solution_set_path="",
        sources=[dict(source.metadata) for source in scoped.sources],
    )
    solution = new_solution_set(
        user_id=student.student_id,
        subject_key=component_subject_id or subject_id,
        mode="quiz",
        practice_id=practice.practice_id,
        solution_set=json.dumps(raw_questions, ensure_ascii=False),
    )
    solution_row = save_solution_set(solution, config)
    practice = replace(practice, solution_set_path=solution_row["path"])
    save_generated_quiz(practice, config)
    return QuizApiResult(
        quiz_id=practice.practice_id,
        title=title,
        difficulty=difficulty_used,
        questions=visible_questions,
        sources=scoped.sources,
        used_model=config.generation_model,
        created_at=datetime.now(timezone.utc),
    )
