"""Contract tests for strict Lovable-facing Pydantic models and adapters."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.api.schemas.adapters import grading_result_from_points, source_snippet_from_chunk, subject_to_model
from src.api.schemas.chat import ChatRequest, ChatResponse, RetrievalSummary, SourceSnippet
from src.api.schemas.feedback import FeedbackEntry
from src.api.schemas.quiz import QuizQuestion
from src.subject_registry import subjects_for_display
from src.vector_store import RetrievedChunk


def _valid_chat(**updates) -> dict:
    payload = {
        "thread_id": "thread-1",
        "subject_id": "history",
        "component_subject_id": None,
        "language": "en",
        "academic_year": "2026/27",
        "grade_level": 11,
        "question": "What caused the event?",
        "learning_goal_id": None,
        "material_ids": [],
        "top_k": 6,
        "include_sources": True,
        "stream": False,
    }
    payload.update(updates)
    return payload


def test_chat_contract_validates_subject_component_language_and_bounds() -> None:
    """Chat input follows the frozen explicit subject/language contract."""
    request = ChatRequest.model_validate(_valid_chat())
    assert request.language == "en" and request.top_k == 6

    combined = ChatRequest.model_validate(
        _valid_chat(
            subject_id="spf_biology_chemistry",
            component_subject_id="spf_chemistry",
            language="de",
        )
    )
    assert combined.component_subject_id == "spf_chemistry"

    invalid_payloads = [
        _valid_chat(subject_id="spf_biology"),
        _valid_chat(component_subject_id="spf_biology"),
        _valid_chat(language="de"),
        _valid_chat(question="   "),
        _valid_chat(question="x" * 4001),
        _valid_chat(top_k=0),
        _valid_chat(unknown_field=True),
    ]
    for payload in invalid_payloads:
        with pytest.raises(ValidationError):
            ChatRequest.model_validate(payload)


def test_subject_and_source_adapters_preserve_real_metadata(temp_config) -> None:
    """Adapters expose 15 subjects and never invent source page/URL fields."""
    subjects = [subject_to_model(subject, config=temp_config) for subject in subjects_for_display(temp_config)]
    assert len(subjects) == 15
    spf = next(subject for subject in subjects if subject.subject_id == "spf_biology_chemistry")
    assert [component.subject_id for component in spf.components] == ["spf_biology", "spf_chemistry"]

    source = source_snippet_from_chunk(
        RetrievedChunk("Real excerpt", {"chunk_id": "chunk-1", "source_name": "notes.md"}, 0.75)
    )
    assert source.source_id == "chunk-1"
    assert source.page is None
    assert source.url is None
    assert source.snippet == "Real excerpt"


def test_exact_grading_and_question_types() -> None:
    """API grading remains unrounded and question types are closed."""
    result = grading_result_from_points(
        points_awarded=1,
        max_points=3,
        rubric_used=["criterion"],
        used_model="fake",
    )
    assert result.swiss_grade == 1 / 3 * 5 + 1
    assert result.swiss_grade != round(result.swiss_grade * 2) / 2

    question = QuizQuestion(
        question_id="q1",
        question_type="multiple_choice",
        prompt="Choose",
        options=["A", "B"],
    )
    assert question.question_type == "multiple_choice"
    with pytest.raises(ValidationError):
        QuizQuestion(
            question_id="q2",
            question_type="essay",
            prompt="Write",
        )


def test_response_timestamps_serialize_as_iso_utc_and_feedback_scopes() -> None:
    """Response timestamps and feedback subject IDs retain contract rules."""
    response = ChatResponse(
        thread_id="t",
        message_id="m",
        answer="Answer",
        sources=[
            SourceSnippet(source_id="s", material_name="note", snippet="text")
        ],
        exam_tip=None,
        used_model="fake",
        retrieval_summary=RetrievalSummary(
            chunks_considered=1,
            chunks_used=1,
            collection_names=["user_x__subject_history"],
        ),
        language="en",
        created_at=datetime(2026, 8, 18, tzinfo=timezone.utc),
    )
    assert response.model_dump(mode="json")["created_at"].endswith("Z")
    with pytest.raises(ValidationError):
        FeedbackEntry(subject_id="spf_biology", feature="chat", rating=5)

