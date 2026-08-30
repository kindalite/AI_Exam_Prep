"""Focused tests for framework-neutral service orchestration."""

from __future__ import annotations

from src.llm_client import LLMResponse
from src.retrieval import StudyContext
from src.services.chat_service import run_chat
from src.services.feedback_service import submit_feedback
from src.services.grading_service import calculate_swiss_grade
from src.services.health_service import get_health
from src.services.material_service import rebuild_subject_index, save_uploaded_material
from src.services.subject_service import list_subjects, read_learning_goals
from src.subject_registry import build_subject_registry
from src.vector_store import InMemoryVectorStore


def test_chat_service_runs_with_injected_retrieval_and_model(temp_config) -> None:
    """The complete chat service should run without Streamlit or external services."""
    subject = build_subject_registry(temp_config)["history"]

    def fake_retrieve(*args, **kwargs) -> StudyContext:
        return StudyContext("local notes", "", "", "", [], [], False)

    def fake_model(prompt, system_prompt, config) -> LLMResponse:
        assert "local notes" in prompt
        assert subject.display_name in system_prompt
        assert config is temp_config
        return LLMResponse("grounded answer", True)

    result = run_chat(
        subject=subject,
        language="English",
        question="What happened?",
        user_id="student",
        config=temp_config,
        persist_history=False,
        retrieve=fake_retrieve,
        call_llm=fake_model,
    )

    assert result.ok
    assert result.response.text == "grounded answer"
    assert result.context.local_context == "local notes"


def test_subject_material_feedback_and_health_services(temp_config) -> None:
    """Non-chat services should operate on explicit temporary context."""
    subjects = list_subjects(temp_config)
    subject = next(item for item in subjects if item.key == "german")
    imported = save_uploaded_material(b"Grammar notes", "grammar.md", subject)
    assert imported.path.read_bytes() == b"Grammar notes"
    assert rebuild_subject_index(subject, temp_config, vector_store=InMemoryVectorStore()) > 0
    assert "Learning Goals" in read_learning_goals(subject)

    feedback = submit_feedback(
        subject_key=subject.key,
        feature="chat",
        user_task="task",
        app_answer="answer",
        rating=4,
        comment="useful",
        config=temp_config,
    )
    assert feedback["rating"] == 4
    assert calculate_swiss_grade(8, 10).grade == 5.0
    assert get_health().status == "ok"

