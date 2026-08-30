"""Generation-provider adapters for Ollama and OpenAI-compatible/vLLM APIs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Protocol
from urllib.parse import urlsplit

import requests

from .config import AppConfig
from .model_types import LLMResponse, ProviderStatus
from .ollama_model_manager import is_model_available, is_ollama_server_reachable


class GenerationProvider(Protocol):
    """Capabilities required by model-agnostic generation services."""

    def generate(self, prompt: str, system_prompt: str | None = None, images: list[Path] | None = None) -> LLMResponse: ...
    def stream(self, prompt: str, system_prompt: str | None = None) -> Iterator[str]: ...
    def status(self) -> ProviderStatus: ...


_OLLAMA_SESSION: requests.Session | None = None


def get_ollama_http_session() -> requests.Session:
    """Return the reused Ollama HTTP session."""
    global _OLLAMA_SESSION
    if _OLLAMA_SESSION is None:
        _OLLAMA_SESSION = requests.Session()
    return _OLLAMA_SESSION


def build_ollama_chat_payload(
    prompt: str,
    system_prompt: str | None,
    model: str,
    *,
    stream: bool = False,
    images: list[str] | None = None,
) -> dict:
    """Build the native Ollama chat payload with keep-alive."""
    messages = _messages(prompt, system_prompt)
    if images:
        messages[-1]["images"] = images
    return {"model": model, "messages": messages, "stream": stream, "keep_alive": "10m"}


def safe_endpoint(endpoint: str) -> str:
    """Return scheme/host/port/path with credentials and query removed."""
    parsed = urlsplit(endpoint)
    if not parsed.hostname:
        return ""
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.hostname}{port}{path}"


def _messages(prompt: str, system_prompt: str | None) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    return messages


class OllamaProvider:
    """Local Ollama adapter preserving keep-alive and vision support."""

    supports_streaming = True

    def __init__(self, config: AppConfig, session: requests.Session | None = None) -> None:
        self.config = config
        self.session = session or get_ollama_http_session()

    def generate(self, prompt: str, system_prompt: str | None = None, images: list[Path] | None = None) -> LLMResponse:
        if not self.config.ollama_host:
            return LLMResponse("", False, "OLLAMA_HOST is missing. Set it in .env.")
        model = self.config.ollama_vision_model if images else self.config.ollama_model
        try:
            encoded = None
            if images:
                import base64

                encoded = [base64.b64encode(Path(path).read_bytes()).decode("ascii") for path in images]
            payload = build_ollama_chat_payload(prompt, system_prompt, model, images=encoded)
            response = self.session.post(
                self.config.ollama_host.rstrip("/") + "/api/chat",
                json=payload,
                timeout=60,
            )
            if response.status_code == 404:
                return LLMResponse("", False, f"The required local model {model} is unavailable.")
            response.raise_for_status()
            data = response.json()
            return LLMResponse(str(data.get("message", {}).get("content", "")), True)
        except OSError as exc:
            return LLMResponse("", False, f"Could not read local image: {exc.__class__.__name__}")
        except requests.RequestException as exc:
            return LLMResponse("", False, f"Ollama is unreachable at {safe_endpoint(self.config.ollama_host)}: {exc.__class__.__name__}")
        except ValueError as exc:
            return LLMResponse("", False, f"Ollama returned invalid JSON: {exc.__class__.__name__}")

    def stream(self, prompt: str, system_prompt: str | None = None) -> Iterator[str]:
        payload = build_ollama_chat_payload(prompt, system_prompt, self.config.ollama_model, stream=True)
        response = self.session.post(
            self.config.ollama_host.rstrip("/") + "/api/chat",
            json=payload,
            timeout=60,
            stream=True,
        )
        try:
            response.raise_for_status()
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except ValueError:
                    continue
                token = str(data.get("message", {}).get("content", ""))
                if token:
                    yield token
        finally:
            if hasattr(response, "close"):
                response.close()

    def status(self) -> ProviderStatus:
        model = self.config.ollama_required_model or self.config.ollama_model
        reachable = is_ollama_server_reachable(self.config.ollama_host)
        available = is_model_available(model, self.config.ollama_host) if reachable else False
        if not reachable:
            message = "Ollama is not reachable. Start the selected local provider."
        elif not available:
            message = f"Required local model {model} is not available."
        else:
            message = f"Local Ollama model {model} is ready."
        hostname = urlsplit(self.config.ollama_host).hostname or ""
        return ProviderStatus(
            provider="ollama",
            model=model,
            endpoint=safe_endpoint(self.config.ollama_host),
            mode="local" if hostname in {"localhost", "127.0.0.1", "::1"} else "remote",
            reachable=reachable and available,
            message=message,
            supports_streaming=True,
            supports_vision=True,
        )


class OpenAICompatibleProvider:
    """Remote OpenAI chat-completions adapter suitable for vLLM."""

    supports_streaming = True

    def __init__(self, config: AppConfig, session: requests.Session | None = None) -> None:
        self.config = config
        self.session = session or requests.Session()

    @property
    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.remote_llm_api_key:
            headers["Authorization"] = f"Bearer {self.config.remote_llm_api_key}"
        return headers

    @property
    def _chat_url(self) -> str:
        return safe_endpoint(self.config.remote_llm_base_url).rstrip("/") + "/chat/completions"

    def generate(self, prompt: str, system_prompt: str | None = None, images: list[Path] | None = None) -> LLMResponse:
        if images:
            return LLMResponse("", False, "The selected remote provider has no configured vision capability; OCR/image description fallback is required.")
        if not self.config.remote_llm_base_url or not self.config.remote_llm_model:
            return LLMResponse("", False, "Remote model base URL and model name must be configured.")
        payload = {"model": self.config.remote_llm_model, "messages": _messages(prompt, system_prompt), "stream": False}
        try:
            response = self.session.post(
                self._chat_url,
                headers=self._headers,
                json=payload,
                timeout=self.config.remote_llm_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return LLMResponse(str(content), bool(str(content).strip()), None if str(content).strip() else "Remote model returned an empty answer.")
        except requests.RequestException as exc:
            return LLMResponse("", False, f"Remote model is unreachable at {safe_endpoint(self.config.remote_llm_base_url)}: {exc.__class__.__name__}")
        except (ValueError, IndexError, KeyError) as exc:
            return LLMResponse("", False, f"Remote model returned an invalid response: {exc.__class__.__name__}")

    def stream(self, prompt: str, system_prompt: str | None = None) -> Iterator[str]:
        payload = {"model": self.config.remote_llm_model, "messages": _messages(prompt, system_prompt), "stream": True}
        response = self.session.post(
            self._chat_url,
            headers=self._headers,
            json=payload,
            timeout=self.config.remote_llm_timeout_seconds,
            stream=True,
        )
        try:
            response.raise_for_status()
            for raw in response.iter_lines(decode_unicode=True):
                if not raw or not raw.startswith("data:"):
                    continue
                value = raw[5:].strip()
                if value == "[DONE]":
                    break
                try:
                    data = json.loads(value)
                except ValueError:
                    continue
                token = str(data.get("choices", [{}])[0].get("delta", {}).get("content", ""))
                if token:
                    yield token
        finally:
            if hasattr(response, "close"):
                response.close()

    def status(self) -> ProviderStatus:
        reachable = False
        message = "Remote provider is not configured."
        if self.config.remote_llm_base_url and self.config.remote_llm_model:
            try:
                response = self.session.get(
                    safe_endpoint(self.config.remote_llm_base_url).rstrip("/") + "/models",
                    headers=self._headers,
                    timeout=self.config.remote_llm_timeout_seconds,
                )
                response.raise_for_status()
                reachable = True
                message = "Remote OpenAI-compatible model endpoint is reachable."
            except requests.RequestException as exc:
                message = f"Remote model endpoint is unreachable: {exc.__class__.__name__}"
        hostname = urlsplit(self.config.remote_llm_base_url).hostname or ""
        return ProviderStatus(
            provider=self.config.model_provider.lower(),
            model=self.config.remote_llm_model,
            endpoint=safe_endpoint(self.config.remote_llm_base_url),
            mode="local" if hostname in {"localhost", "127.0.0.1", "::1"} else "remote",
            reachable=reachable,
            message=message,
            supports_streaming=True,
            supports_vision=False,
        )


def build_model_provider(config: AppConfig, *, session: requests.Session | None = None) -> GenerationProvider:
    """Select the configured provider without exposing provider details to callers."""
    selected = config.model_provider.strip().lower()
    if selected == "ollama":
        return OllamaProvider(config, session=session)
    if selected in {"openai_compatible", "vllm"}:
        return OpenAICompatibleProvider(config, session=session)
    raise ValueError(f"Unsupported MODEL_PROVIDER: {config.model_provider}")
