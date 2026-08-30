"""Framework-neutral study-plan generation service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Callable

from ..config import AppConfig
from ..llm_client import LLMResponse, generate_response
from ..prompts import build_study_plan_prompt, build_system_prompt
from ..retrieval import sources_to_context
from ..study_plan_generator import create_study_plan
from ..subject_languages import language_name
from ..subject_registry import Subject, get_subject
from ..vector_store import RetrievedChunk
from .chat_service import learning_goal_context, retrieve_scoped_evidence
from .identity_service import StudentContext
from .structured_output import call_structured_model


def generate_study_plan(
    subject: Subject,
    language: str,
    exam_date: str,
    hours_per_week: float,
    weak_topics: str,
    *,
    call_llm: bool = True,
) -> LLMResponse:
    """Generate a study-plan proposal through the existing implementation."""
    return create_study_plan(
        subject,
        language,
        exam_date,
        hours_per_week,
        weak_topics,
        call_llm=call_llm,
    )


@dataclass(frozen=True)
class StudyPlanItemResult:
    """One non-overlapping scheduled proposal item."""

    item_id: str
    date: date
    start_time: str
    end_time: str
    title: str
    description: str
    duration_minutes: int
    activity_type: str
    learning_goal_id: str | None


@dataclass(frozen=True)
class StudyPlanApiResult:
    """Structured plan proposal; frontend planner state is never mutated."""

    study_plan_id: str
    exam_date: date
    items: tuple[StudyPlanItemResult, ...]
    summary: str
    sources: tuple[RetrievedChunk, ...]
    used_model: str
    created_at: datetime


def _minutes(value: str) -> int:
    parsed = time.fromisoformat(value)
    return parsed.hour * 60 + parsed.minute


def _default_slots(exam_date: date) -> list[dict]:
    slots: list[dict] = []
    day = date.today()
    while day < exam_date and len(slots) < 60:
        slots.append({"date": day, "start_time": "18:00", "end_time": "20:00"})
        day += timedelta(days=1)
    return slots


def _validate_plan_payload(value: dict) -> tuple[str, list[dict]]:
    summary = str(value.get("summary", "")).strip()
    tasks = value.get("items")
    if not summary or not isinstance(tasks, list) or not tasks:
        raise ValueError("A summary and at least one plan item are required")
    allowed = {"review", "practice", "quiz", "mock_exam", "break"}
    normalized: list[dict] = []
    for index, raw in enumerate(tasks, start=1):
        if not isinstance(raw, dict):
            raise ValueError("Every plan item must be an object")
        title = str(raw.get("title", "")).strip()
        description = str(raw.get("description", "")).strip()
        duration = int(raw.get("duration_minutes", 0))
        activity = str(raw.get("activity_type", ""))
        if not title or not description or duration <= 0 or activity not in allowed:
            raise ValueError(f"Plan item {index} is malformed")
        normalized.append(
            {
                "title": title,
                "description": description,
                "duration_minutes": duration,
                "activity_type": activity,
                "learning_goal_id": raw.get("learning_goal_id"),
            }
        )
    return summary, normalized


def _schedule_items(
    tasks: list[dict], slots: list[dict], exam_date: date, max_daily_minutes: int
) -> tuple[StudyPlanItemResult, ...]:
    normalized_slots: list[tuple[date, int, int]] = []
    for slot in slots or _default_slots(exam_date):
        slot_date = slot["date"]
        if isinstance(slot_date, str):
            slot_date = date.fromisoformat(slot_date)
        start = _minutes(str(slot["start_time"]))
        end = _minutes(str(slot["end_time"]))
        if slot_date < date.today() or slot_date >= exam_date or end <= start:
            raise ValueError("Available slots must be future windows ending before the exam")
        normalized_slots.append((slot_date, start, end))
    normalized_slots.sort()
    daily_used: dict[date, int] = {}
    cursors: dict[int, int] = {index: start for index, (_day, start, _end) in enumerate(normalized_slots)}
    scheduled: list[StudyPlanItemResult] = []
    for item_index, task in enumerate(tasks, start=1):
        duration = min(int(task["duration_minutes"]), max_daily_minutes)
        selected: tuple[int, date, int] | None = None
        for slot_index, (slot_date, _start, end) in enumerate(normalized_slots):
            cursor = cursors[slot_index]
            if cursor + duration <= end and daily_used.get(slot_date, 0) + duration <= max_daily_minutes:
                selected = (slot_index, slot_date, cursor)
                break
        if selected is None:
            raise ValueError("The proposed items do not fit the available non-overlapping slots")
        slot_index, slot_date, start = selected
        end = start + duration
        cursors[slot_index] = end
        daily_used[slot_date] = daily_used.get(slot_date, 0) + duration
        format_time = lambda minute: f"{minute // 60:02d}:{minute % 60:02d}"
        scheduled.append(
            StudyPlanItemResult(
                item_id=f"item_{item_index}",
                date=slot_date,
                start_time=format_time(start),
                end_time=format_time(end),
                title=task["title"],
                description=task["description"],
                duration_minutes=duration,
                activity_type=task["activity_type"],
                learning_goal_id=(str(task["learning_goal_id"]) if task.get("learning_goal_id") else None),
            )
        )
    return tuple(scheduled)


def generate_study_plan_api(
    *,
    subject_id: str,
    component_subject_id: str | None,
    language: str,
    exam_date: date,
    hours_per_week: float,
    weak_topics: list[str],
    learning_goal_ids: list[str],
    available_time_slots: list[dict],
    max_daily_minutes: int,
    material_ids: list[str],
    student: StudentContext,
    config: AppConfig,
    vector_store=None,
    call_llm: Callable[..., LLMResponse] = generate_response,
) -> StudyPlanApiResult:
    """Generate and deterministically schedule a user-scoped plan proposal."""
    if exam_date <= date.today():
        raise ValueError("exam_date must be in the future")
    subject = get_subject(subject_id, config)
    goals = [
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
    goal_text = "\n".join(goals)
    query = " ".join(weak_topics) or goal_text or "study plan"
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
    prompt = build_study_plan_prompt(
        subject,
        language_name(language),
        exam_date.isoformat(),
        hours_per_week,
        ", ".join(weak_topics),
        sources_to_context(list(scoped.sources)) + "\n" + sources_to_context(list(scoped.memory_sources)),
        goal_text,
    )
    prompt += (
        "\n\nReturn exactly one JSON object with summary and items. Each item must contain title, "
        "description, duration_minutes, activity_type, and optional learning_goal_id. Allowed "
        "activity_type values: review, practice, quiz, mock_exam, break. Do not choose dates or "
        "times; the backend schedules items into validated slots. No Markdown."
    )
    summary, tasks = call_structured_model(
        prompt=prompt,
        system_prompt=build_system_prompt(subject, language),
        config=config,
        call_llm=call_llm,
        validate=_validate_plan_payload,
    )
    slot_rows = [slot.model_dump(mode="python") if hasattr(slot, "model_dump") else dict(slot) for slot in available_time_slots]
    items = _schedule_items(tasks, slot_rows, exam_date, max_daily_minutes)
    seed = f"{student.student_id}|{subject_id}|{exam_date.isoformat()}|{datetime.now(timezone.utc).isoformat()}"
    import hashlib

    plan_id = "plan_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20]
    return StudyPlanApiResult(
        study_plan_id=plan_id,
        exam_date=exam_date,
        items=items,
        summary=summary,
        sources=scoped.sources,
        used_model=config.generation_model,
        created_at=datetime.now(timezone.utc),
    )
