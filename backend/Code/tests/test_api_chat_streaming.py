"""SSE chat event order, metadata, failures, and iterator cleanup tests."""

from __future__ import annotations

import json
from dataclasses import replace
from functools import partial

from fastapi.testclient import TestClient

from src.ai_metadata_store import find_ai_provenance
from src.api.dependencies import ApiServices, get_api_services, get_config
from src.api.main import create_app
from src.chunking import TextChunk
from src.services.chat_service import (
    ChatModelUnavailableError,
    finalize_api_chat,
    open_api_chat_stream,
    prepare_api_chat,
)
from src.services.identity_service import StudentContext
from src.user_data_paths import user_subject_collection_name
from src.vector_store import InMemoryVectorStore


def _payload() -> dict:
    return {
        "thread_id": "stream-thread",
        "subject_id": "history",
        "component_subject_id": None,
        "language": "en",
        "academic_year": "2026/27",
        "grade_level": 11,
        "question": "Explain the source.",
        "learning_goal_id": None,
        "material_ids": [],
        "top_k": 4,
        "include_sources": True,
        "stream": True,
    }


def _events(text: str) -> list[tuple[str, dict]]:
    parsed = []
    for block in text.strip().split("\n\n"):
        lines = block.splitlines()
        event = next(line[7:] for line in lines if line.startswith("event: "))
        data = json.loads(next(line[6:] for line in lines if line.startswith("data: ")))
        parsed.append((event, data))
    return parsed


def _store() -> InMemoryVectorStore:
    store = InMemoryVectorStore()
    store.rebuild_collection(
        user_subject_collection_name("student-a", "history"),
        [
            TextChunk(
                "Primary source evidence",
                {
                    "chunk_id": "source-1",
                    "source_name": "source.md",
                    "material_id": "mat_source",
                    "user_id": "student-a",
                },
            )
        ],
    )
    return store


def _client(temp_config, tokens_factory):
    store = _store()
    app = create_app()
    app.dependency_overrides[get_config] = lambda: temp_config
    app.dependency_overrides[get_api_services] = lambda: replace(
        ApiServices(),
        chat=lambda **kwargs: (_ for _ in ()).throw(AssertionError("non-streaming model called")),
        prepare_chat=partial(prepare_api_chat, vector_store=store),
        open_chat_stream=lambda prepared, config: tokens_factory(),
        finalize_chat=finalize_api_chat,
    )
    return TestClient(app)


def test_sse_token_order_concatenation_done_metadata_and_single_generation(temp_config) -> None:
    """Tokens arrive in order and one final event retains all grounded metadata."""
    calls = 0

    def tokens():
        nonlocal calls
        calls += 1
        yield "Grounded "
        yield "answer"

    with _client(temp_config, tokens) as client:
        response = client.post(
            "/api/chat", json=_payload(), headers={"X-Student-Id": "student-a"}
        )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _events(response.text)
    assert [event for event, _data in events] == ["token", "token", "done"]
    assert "".join(data["delta"] for event, data in events if event == "token") == "Grounded answer"
    done = events[-1][1]
    assert done["sources"][0]["material_id"] == "mat_source"
    assert done["retrieval_summary"]["chunks_used"] == 1
    assert calls == 1
    assert find_ai_provenance("student-a", "stream-thread", done["message_id"], temp_config)


def test_stream_failure_before_tokens_is_normal_http_error(temp_config) -> None:
    """An empty/failing provider before headers returns the common JSON error envelope."""
    with _client(temp_config, lambda: iter(())) as client:
        response = client.post(
            "/api/chat", json=_payload(), headers={"X-Student-Id": "student-a"}
        )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_unavailable"


def test_stream_failure_after_token_emits_error_and_closes(temp_config) -> None:
    """Post-header failures emit one SSE error and release the provider iterator."""
    state = {"closed": False}

    def tokens():
        try:
            yield "partial"
            raise RuntimeError("provider disconnected")
        finally:
            state["closed"] = True

    with _client(temp_config, tokens) as client:
        response = client.post(
            "/api/chat", json=_payload(), headers={"X-Student-Id": "student-a"}
        )
    events = _events(response.text)
    assert [event for event, _data in events] == ["token", "error"]
    assert events[-1][1]["code"] == "stream_failed"
    assert state["closed"] is True


def test_provider_without_streaming_fails_predictably_and_iterator_can_cancel(temp_config) -> None:
    """Unsupported capability errors are explicit; closing an active iterator runs cleanup."""
    prepared = prepare_api_chat(
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
    )

    class NoStreaming:
        supports_streaming = False

    try:
        open_api_chat_stream(prepared, config=temp_config, provider=NoStreaming())
    except ChatModelUnavailableError as exc:
        assert "does not support" in str(exc)
    else:
        raise AssertionError("non-streaming provider was accepted")

    state = {"closed": False}

    class Streaming:
        supports_streaming = True

        def stream(self, prompt, system_prompt=None):
            try:
                yield "first"
                yield "second"
            finally:
                state["closed"] = True

    iterator = open_api_chat_stream(prepared, config=temp_config, provider=Streaming())
    assert next(iterator) == "first"
    iterator.close()
    assert state["closed"] is True
