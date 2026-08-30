# Prompt 13 — Add SSE Streaming to `/api/chat` Without Breaking JSON Mode

Only do this after the non-streaming chat endpoint is stable and contract-tested.

## Contract

When `stream:false`, preserve the existing JSON response exactly.

When `stream:true`, return `text/event-stream` with events:

```text
event: token
data: {"delta":"..."}

event: done
data: {"message_id":"...","sources":[...],"exam_tip":"...","used_model":"...","retrieval_summary":{...},"created_at":"..."}
```

For failures before tokens, return normal structured HTTP errors where possible. For failures after streaming begins, emit a structured `event: error` and close cleanly.

## Tasks

1. Reuse existing `model_runtime.stream_chat_tokens` or provider streaming interface; do not perform a second model call just to obtain metadata.
2. Perform retrieval/prompt construction before starting the event stream where practical so validation/retrieval errors can still return HTTP status codes.
3. Detect client disconnect/cancellation and stop downstream generation if the provider supports it; otherwise stop yielding and release local resources.
4. Preserve source/exam-tip/model metadata in the final `done` event.
5. Keep Supabase transcript ownership outside Python in Stage 1.
6. Avoid buffering the whole answer before emitting tokens.
7. Add heartbeat/comment events only if required to prevent timeouts; keep the frontend parser simple.
8. Add streaming tests that verify event order, token concatenation, final metadata, client cancellation, and model failure.
9. Keep non-streaming tests unchanged and green.
10. Document any provider that cannot stream and implement a predictable fallback/error rather than pretending token streaming.

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
