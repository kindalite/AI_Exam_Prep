"""Stage-1 non-streaming chat/RAG API contract and isolation tests."""

from __future__ import annotations

from functools import partial

import pytest
from fastapi.testclient import TestClient

from src.ai_metadata_store import find_ai_provenance
from src.api.dependencies import ApiServices, get_api_services, get_config
from src.api.main import create_app
from src.chunking import TextChunk
from src.llm_client import LLMResponse
from src.services.chat_service import ChatModelUnavailableError, run_api_chat
from src.services.identity_service import StudentContext
from src.services.subject_service import list_learning_goals
from src.subject_registry import get_subject
from src.user_data_paths import user_memory_collection_name, user_subject_collection_name
from src.vector_store import InMemoryVectorStore


def _chunk(text: str, *, user_id: str | None = None, material_id: str = "mat_one") -> TextChunk:
    metadata = {
        "chunk_id": f"chunk_{material_id}_{text[:6]}",
        "source_name": f"{material_id}.md",
        "original_name": f"{material_id}.md",
        "material_id": material_id,
        "source_layer": "user_material" if user_id else "canonical",
        "section": "topic",
    }
    if user_id:
        metadata["user_id"] = user_id
    return TextChunk(text, metadata)


def _payload(**updates) -> dict:
    payload = {
        "thread_id": "thread-1",
        "subject_id": "history",
        "component_subject_id": None,
        "language": "en",
        "academic_year": "2026/27",
        "grade_level": 11,
        "question": "Explain the causes.",
        "learning_goal_id": None,
        "material_ids": [],
        "top_k": 6,
        "include_sources": True,
        "stream": False,
    }
    payload.update(updates)
    return payload


def _fake_model(captured: list[str]):
    def call(prompt, system_prompt, config):
        captured.append(prompt + "\n" + system_prompt)
        return LLMResponse("Grounded answer", True)

    return call


def _client(temp_config, store, model):
    app = create_app()
    app.dependency_overrides[get_config] = lambda: temp_config
    app.dependency_overrides[get_api_services] = lambda: ApiServices(
        chat=partial(run_api_chat, vector_store=store, call_llm=model)
    )
    return TestClient(app)


def test_normal_chat_exact_shape_material_filter_and_no_transcript(temp_config) -> None:
    """Normal chat filters materials and does not create Python chat history."""
    store = InMemoryVectorStore()
    store.rebuild_collection(
        user_subject_collection_name("student-a", "history"),
        [_chunk("selected private evidence", user_id="student-a", material_id="mat_one"),
         _chunk("excluded private evidence", user_id="student-a", material_id="mat_two"),
         _chunk("foreign evidence", user_id="student-b", material_id="mat_one")],
    )
    store.rebuild_collection(
        get_subject("history", temp_config).collection_name,
        [_chunk("selected canonical evidence", material_id="mat_one")],
    )
    store.rebuild_collection(
        user_memory_collection_name("student-a", "history"),
        [_chunk("student-a performance memory", user_id="student-a", material_id="memory")],
    )
    captured: list[str] = []
    with _client(temp_config, store, _fake_model(captured)) as client:
        response = client.post(
            "/api/chat",
            json=_payload(material_ids=["mat_one"]),
            headers={"X-Student-Id": "student-a"},
        )
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "thread_id", "message_id", "answer", "sources", "exam_tip", "used_model",
        "retrieval_summary", "language", "created_at",
    }
    assert body["message_id"].startswith("ai_")
    assert {source["material_id"] for source in body["sources"]} == {"mat_one"}
    assert body["retrieval_summary"]["material_ids"] == ["mat_one"]
    assert "excluded private evidence" not in captured[0]
    assert "foreign evidence" not in captured[0]
    assert "student-a performance memory" in captured[0]
    assert not (temp_config.data_dir / "users" / "student-a" / "chat_history" / "messages.jsonl").exists()
    provenance = find_ai_provenance("student-a", "thread-1", body["message_id"], temp_config)
    assert provenance is not None
    assert provenance["material_ids"] == ["mat_one"]
    assert "answer" not in provenance and "question" not in provenance


@pytest.mark.parametrize(
    ("subject_id", "language", "instruction"),
    [("biology", "de", "German"), ("history", "en", "English"), ("french", "fr", "CEFR B1 French")],
)
def test_each_language_and_empty_material_scope(
    temp_config, subject_id: str, language: str, instruction: str
) -> None:
    """All three frozen language contracts reach the model unchanged."""
    store = InMemoryVectorStore()
    store.rebuild_collection(
        user_subject_collection_name("student-a", subject_id),
        [_chunk("unrestricted material", user_id="student-a")],
    )
    captured: list[str] = []
    with _client(temp_config, store, _fake_model(captured)) as client:
        response = client.post(
            "/api/chat",
            json=_payload(subject_id=subject_id, language=language, material_ids=[]),
            headers={"X-Student-Id": "student-a"},
        )
    assert response.status_code == 200
    assert response.json()["language"] == language
    assert instruction in captured[0]
    assert "unrestricted material" in captured[0]


def test_spf_component_and_combined_query_only_resolved_corpora(temp_config) -> None:
    """SPF component selection remains singular while combined mode queries both."""
    store = InMemoryVectorStore()
    for key, text in (("spf_biology", "advanced cells"), ("spf_chemistry", "advanced ions")):
        store.rebuild_collection(
            user_subject_collection_name("student-a", key),
            [_chunk(text, user_id="student-a", material_id=f"mat_{key}")],
        )
    captured: list[str] = []
    model = _fake_model(captured)
    component = run_api_chat(
        subject_id="spf_biology_chemistry",
        component_subject_id="spf_biology",
        language="de",
        question="Explain",
        learning_goal_id=None,
        material_ids=[],
        top_k=6,
        student=StudentContext("student-a"),
        config=temp_config,
        vector_store=store,
        call_llm=model,
    )
    combined = run_api_chat(
        subject_id="spf_biology_chemistry",
        component_subject_id=None,
        language="de",
        question="Explain",
        learning_goal_id=None,
        material_ids=[],
        top_k=6,
        student=StudentContext("student-a"),
        config=temp_config,
        vector_store=store,
        call_llm=model,
    )
    assert "advanced cells" in component.sources[0].text
    assert all("spf_chemistry" not in name for name in component.collection_names)
    assert {source.text for source in combined.sources} == {"advanced cells", "advanced ions"}
    assert any("spf_biology" in name for name in combined.collection_names)
    assert any("spf_chemistry" in name for name in combined.collection_names)


def test_stream_identity_model_and_learning_goal_errors_are_structured(temp_config) -> None:
    """Unsupported streaming, identity, goal, and model failures never return blank 200s."""
    store = InMemoryVectorStore()
    with _client(temp_config, store, lambda *args, **kwargs: LLMResponse("", False, "offline")) as client:
        missing = client.post("/api/chat", json=_payload())
        streaming = client.post(
            "/api/chat", json=_payload(stream=True), headers={"X-Student-Id": "student-a"}
        )
        bad_goal = client.post(
            "/api/chat",
            json=_payload(learning_goal_id="goal_missing"),
            headers={"X-Student-Id": "student-a"},
        )
        unavailable = client.post(
            "/api/chat", json=_payload(), headers={"X-Student-Id": "student-a"}
        )
    assert (missing.status_code, missing.json()["error"]["code"]) == (401, "student_identity_required")
    assert (streaming.status_code, streaming.json()["error"]["code"]) == (503, "model_unavailable")
    assert (bad_goal.status_code, bad_goal.json()["error"]["code"]) == (422, "invalid_learning_goal")
    assert (unavailable.status_code, unavailable.json()["error"]["code"]) == (503, "model_unavailable")


def test_learning_goal_scope_exam_tip_and_hidden_sources(temp_config) -> None:
    """A real goal is scoped explicitly and criteria support an honest exam tip."""
    subject = get_subject("history", temp_config)
    subject.learning_goals_file.write_text(
        "# Causes\n\n- Explain the economic cause.\n- Compare the political cause.\n",
        encoding="utf-8",
    )
    subject.exam_criteria_file.write_text(
        "# Exam Criteria\n\n- Link every claim to a dated event.\n",
        encoding="utf-8",
    )
    goals = list_learning_goals(temp_config, "history")
    selected = goals[0]
    store = InMemoryVectorStore()
    store.rebuild_collection(
        subject.collection_name,
        [_chunk("dated canonical evidence", material_id="mat_dates")],
    )
    captured: list[str] = []
    with _client(temp_config, store, _fake_model(captured)) as client:
        response = client.post(
            "/api/chat",
            json=_payload(learning_goal_id=selected.learning_goal_id, include_sources=False),
            headers={"X-Student-Id": "student-a"},
        )
    body = response.json()
    assert response.status_code == 200
    assert body["sources"] == []
    assert body["retrieval_summary"]["chunks_used"] == 1
    assert body["retrieval_summary"]["learning_goal_id"] == selected.learning_goal_id
    assert selected.text in captured[0]
    assert goals[1].text not in captured[0]
    assert body["exam_tip"] == "Exam focus: Link every claim to a dated event."


def test_service_rejects_blank_model_answer(temp_config) -> None:
    """A nominal model success with blank text is still unavailable."""
    with pytest.raises(ChatModelUnavailableError):
        run_api_chat(
            subject_id="history",
            component_subject_id=None,
            language="en",
            question="Question",
            learning_goal_id=None,
            material_ids=[],
            top_k=2,
            student=StudentContext("student-a"),
            config=temp_config,
            vector_store=InMemoryVectorStore(),
            call_llm=lambda *args, **kwargs: LLMResponse("   ", True),
        )
