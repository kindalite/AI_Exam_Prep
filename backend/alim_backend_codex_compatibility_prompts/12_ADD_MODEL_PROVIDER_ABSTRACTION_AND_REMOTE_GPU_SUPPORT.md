# Prompt 12 — Add Model Provider Abstraction for Local Ollama and Remote OpenAI-Compatible/vLLM

The backend currently implements Ollama even though `MODEL_PROVIDER` is configurable. Make model serving swappable without changing the frontend API.

## Goals

Support at least:

1. `ollama` — local/default (`gemma3:4b` remains a valid default for ~7 GB VRAM demo use).
2. `openai_compatible` / `vllm` — remote GPU endpoint, potentially reachable over a private Tailscale address.

The frontend must see only model status and generated results. Provider secrets remain backend-only.

## Tasks

1. Define a provider interface/protocol with capabilities needed by existing code:
   - non-streaming chat;
   - streaming tokens if supported;
   - health/status/latency;
   - model name/provider/mode;
   - optional image/vision capability metadata.
2. Adapt existing `llm_client.py`, `model_runtime.py`, and Ollama manager behind that interface while preserving current call seams and `LLMResponse` compatibility where practical.
3. Implement an OpenAI-compatible adapter suitable for vLLM. Use backend `.env` settings such as:
   - `MODEL_PROVIDER`
   - `REMOTE_LLM_BASE_URL`
   - `REMOTE_LLM_API_KEY`
   - `REMOTE_LLM_MODEL`
   - `REMOTE_LLM_TIMEOUT_SECONDS`
4. Never return API keys/tokens in status/logs/OpenAPI/errors.
5. `GET /api/model/status` must truthfully return provider, model, safe endpoint, `mode: local|remote`, reachability, latency, embedding model, optional fallback provider.
6. Keep the embedding provider independent from the generation-model provider.
7. Preserve token-budget enforcement across providers.
8. Preserve vision behaviour explicitly: if the selected remote provider cannot accept images, use existing OCR/image-description path or return a capability warning rather than silently dropping images.
9. Add provider-selection tests with fake adapters; existing unit tests must not need a remote server.
10. Add opt-in smoke scripts for local Ollama and remote OpenAI-compatible endpoint.
11. Update environment verification to validate only the selected provider's prerequisites.
12. Document Tailscale/private-network deployment as an optional backend configuration, not a frontend concern. Do not configure Tailscale or expose a public listener from application code.

## Global constraints for this work package

Treat these as non-negotiable unless a later prompt explicitly changes them:

- The Lovable/TanStack frontend contract is the integration target. Wire format is `snake_case`.
- Preserve the existing Python Streamlit application while the API migration is in progress. Do not delete `app.py` or the Streamlit UI modules yet.
- Do not duplicate existing RAG, generation, grading, storage, or model logic inside route handlers. Extract/reuse framework-neutral services.
- Keep all existing tests green unless a test is intentionally updated because the public contract changes; explain every intentional change.
- The frontend remains authoritative for the 15-card display model, visual labels, Swiss-grade display rounding, colours, planner CRUD, grade averages, localStorage prototype state, and SPF combined-grade display logic.
- Python becomes authoritative for AI inference, RAG, document parsing/indexing, learning goals, exam criteria, quizzes, mock exams, AI grading, study-plan proposals, feedback persistence, source metadata, and model health.
- Stage 1 keeps Supabase authentication and chat thread/message persistence. The Python API must not become a second authoritative chat-transcript writer.
- Browser code must never talk directly to Chroma, Ollama, vLLM, or another model provider.
- Bind the Python API to `127.0.0.1` by default. Do not expose it publicly.
- `X-Student-Id` is the Stage-1 local identity bridge for user-scoped API operations. Sanitize it with the existing user-path helpers before it can influence paths or collection names.
- Do not weaken the backend's existing privacy rules for public-web retrieval. Private notes must not be sent to public search by default.
- Preserve hidden-solution rules for quizzes/exams.
- Preserve graceful degradation for optional OCR, image, audio, web, and vector dependencies.
- Add docstrings/comments for new public functions and non-obvious logic, but do not add noisy comments that merely restate syntax line-by-line.
- Prefer dependency injection and existing fake seams over global monkey-patching so tests can run without Ollama/network/Chroma.
- After each work package, run the focused tests first and then the broad regression suite where practical. Report commands and results.
