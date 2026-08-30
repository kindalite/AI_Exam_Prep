"""Provider selection, remote protocol, capability, and secret-safety tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import requests

from src.llm_client import generate_response
from src.model_providers import OllamaProvider, OpenAICompatibleProvider, build_model_provider
from src.model_types import LLMResponse, ProviderStatus
from src.services.health_service import get_model_status_snapshot


class FakeResponse:
    def __init__(self, payload=None, lines=None, status_code=200):
        self.payload = payload or {}
        self.lines = lines or []
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("safe fake failure")

    def json(self):
        return self.payload

    def iter_lines(self, decode_unicode=True):
        return iter(self.lines)


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        if kwargs.get("stream"):
            return FakeResponse(lines=['data: {"choices":[{"delta":{"content":"Hi"}}]}', "data: [DONE]"])
        return FakeResponse({"choices": [{"message": {"content": "remote answer"}}]})

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return FakeResponse({"data": [{"id": "remote-model"}]})


def _remote_config(temp_config):
    return replace(
        temp_config,
        model_provider="vllm",
        remote_llm_base_url="https://user:password@100.64.0.5:8000/v1?token=query-secret",
        remote_llm_api_key="backend-secret",
        remote_llm_model="remote-model",
        remote_llm_timeout_seconds=9,
        embedding_model="independent-embedding",
    )


def test_provider_selection_and_remote_nonstreaming_streaming(temp_config) -> None:
    """The factory selects adapters and the remote wire format matches chat completions."""
    assert isinstance(build_model_provider(temp_config), OllamaProvider)
    session = FakeSession()
    config = _remote_config(temp_config)
    provider = build_model_provider(config, session=session)
    assert isinstance(provider, OpenAICompatibleProvider)
    response = generate_response("Question", "System", config=config, provider=provider)
    assert response == LLMResponse("remote answer", True)
    assert list(provider.stream("Question", "System")) == ["Hi"]
    post = session.calls[0]
    assert post[1].endswith("/v1/chat/completions")
    assert post[2]["headers"]["Authorization"] == "Bearer backend-secret"
    assert post[2]["json"]["model"] == "remote-model"


def test_remote_status_is_safe_truthful_and_embedding_independent(temp_config) -> None:
    """Status exposes capabilities and sanitized endpoint, never secrets."""
    config = _remote_config(temp_config)
    provider = OpenAICompatibleProvider(config, session=FakeSession())
    status = provider.status()
    assert status.reachable and status.mode == "remote"
    assert status.endpoint == "https://100.64.0.5:8000/v1"
    serialized = repr(status)
    assert "backend-secret" not in serialized and "password" not in serialized and "query-secret" not in serialized

    class FakeProvider:
        def status(self):
            return status

    snapshot = get_model_status_snapshot(config, provider=FakeProvider())
    assert snapshot.provider == "vllm"
    assert snapshot.model == "remote-model"
    assert snapshot.embedding_model == "independent-embedding"
    assert snapshot.supports_streaming is True and snapshot.supports_vision is False


def test_remote_vision_returns_capability_warning_without_upload(temp_config, tmp_path: Path) -> None:
    """An unsupported image is never silently dropped or sent to a text-only server."""
    session = FakeSession()
    provider = OpenAICompatibleProvider(_remote_config(temp_config), session=session)
    image = tmp_path / "image.png"
    image.write_bytes(b"png")
    response = provider.generate("Describe", images=[image])
    assert response.ok is False and "vision capability" in (response.error or "")
    assert session.calls == []


def test_generate_response_accepts_fake_provider_seam(temp_config) -> None:
    """Normal tests can inject a provider without any live server."""
    class FakeProvider:
        def generate(self, prompt, system_prompt=None, images=None):
            return LLMResponse(f"fake:{prompt}", True)

        def stream(self, prompt, system_prompt=None):
            yield "fake"

        def status(self):
            return ProviderStatus("fake", "fake", "", "local", True, "ready", True, False)

    response = generate_response("hello", config=temp_config, provider=FakeProvider())
    assert response.text == "fake:hello"
