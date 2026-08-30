"""Framework-neutral process and model health services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic, perf_counter
from urllib.parse import urlsplit

from ..config import AppConfig
from ..model_providers import build_model_provider
from ..model_runtime import ModelRuntimeStatus, verify_model_runtime, warm_model
from ..subject_registry import TOP_LEVEL_SUBJECT_IDS, corpus_keys_for_request


@dataclass(frozen=True)
class HealthStatus:
    """Lightweight process health independent of model availability."""

    status: str = "ok"
    service: str = "alim-study-assistant"


@dataclass(frozen=True)
class VectorHealth:
    """Safe summary of the configured vector store."""

    store_type: str
    reachable: bool
    collection_count: int
    collection_names: tuple[str, ...] = ()
    message: str = ""


@dataclass(frozen=True)
class ModelStatusSnapshot:
    """Provider-neutral model status suitable for API serialization."""

    provider: str
    model: str
    endpoint: str
    mode: str
    reachable: bool
    latency_ms: float
    embedding_model: str
    fallback_provider: str | None = None
    message: str = ""
    supports_streaming: bool = False
    supports_vision: bool = False


@dataclass(frozen=True)
class ApiHealthSnapshot:
    """Combined API, vector, and model health summary."""

    status: str
    api_version: str
    uptime_seconds: float
    vector_store: VectorHealth
    model_server_reachable: bool
    model_provider: str
    indexed_top_level_subjects: int
    checked_at: str


def get_health() -> HealthStatus:
    """Return process liveness without probing optional dependencies."""
    return HealthStatus()


def get_model_status(config: AppConfig) -> ModelRuntimeStatus:
    """Return the existing model runtime status."""
    return verify_model_runtime(config)


def warm_model_runtime(config: AppConfig, timeout_seconds: int = 30) -> ModelRuntimeStatus:
    """Warm the configured model runtime."""
    return warm_model(config, timeout_seconds=timeout_seconds)


def _safe_endpoint(endpoint: str) -> str:
    """Return only the endpoint scheme and authority, without credentials/query."""
    parsed = urlsplit(endpoint)
    hostname = parsed.hostname or ""
    if not hostname:
        return ""
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{hostname}{port}"


def get_vector_status(config: AppConfig) -> VectorHealth:
    """Probe local Chroma metadata without loading an embedding model."""
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(config.vector_db_dir))
        collections = client.list_collections()
        names = tuple(
            sorted(str(getattr(collection, "name", collection)) for collection in collections)
        )
        return VectorHealth("chroma", True, len(names), names, "Persistent Chroma is reachable.")
    except Exception as exc:
        return VectorHealth("in_memory_fallback", False, 0, (), f"Chroma unavailable: {exc}")


def get_model_status_snapshot(config: AppConfig, *, provider=None) -> ModelStatusSnapshot:
    """Measure current model reachability and return safe provider metadata."""
    started = perf_counter()
    try:
        provider_status = (provider or build_model_provider(config)).status()
    except ValueError as exc:
        provider_status = None
        error_message = str(exc)
    latency_ms = round((perf_counter() - started) * 1000, 2)
    fallback = getattr(config, "fallback_model_provider", None)
    if provider_status is None:
        endpoint = _safe_endpoint(config.remote_llm_base_url or config.ollama_host)
        hostname = urlsplit(endpoint).hostname or ""
        return ModelStatusSnapshot(
            provider=config.model_provider,
            model=config.remote_llm_model or config.ollama_model,
            endpoint=endpoint,
            mode="local" if hostname in {"localhost", "127.0.0.1", "::1"} else "remote",
            reachable=False,
            latency_ms=latency_ms,
            embedding_model=config.embedding_model,
            fallback_provider=fallback or None,
            message=error_message,
        )
    return ModelStatusSnapshot(
        provider=provider_status.provider,
        model=provider_status.model,
        endpoint=provider_status.endpoint,
        mode=provider_status.mode,
        reachable=provider_status.reachable,
        latency_ms=latency_ms,
        embedding_model=config.embedding_model,
        fallback_provider=fallback or None,
        message=provider_status.message,
        supports_streaming=provider_status.supports_streaming,
        supports_vision=provider_status.supports_vision,
    )


def get_api_health(
    config: AppConfig,
    started_monotonic: float,
    *,
    api_version: str,
    vector_status: VectorHealth | None = None,
    model_status: ModelStatusSnapshot | None = None,
) -> ApiHealthSnapshot:
    """Build a complete health snapshot from existing runtime probes."""
    vector = vector_status or get_vector_status(config)
    model = model_status or get_model_status_snapshot(config)
    collection_names = set(vector.collection_names)
    indexed_count = 0
    for subject_id in TOP_LEVEL_SUBJECT_IDS:
        corpora = corpus_keys_for_request(subject_id)
        if any(f"subject_{key}" in collection_names for key in corpora):
            indexed_count += 1
    status = "ok" if vector.reachable and model.reachable else "degraded"
    return ApiHealthSnapshot(
        status=status,
        api_version=api_version,
        uptime_seconds=round(max(0.0, monotonic() - started_monotonic), 3),
        vector_store=vector,
        model_server_reachable=model.reachable,
        model_provider=model.provider,
        indexed_top_level_subjects=indexed_count,
        checked_at=datetime.now(timezone.utc).isoformat(),
    )
