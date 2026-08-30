# Prompt 11 — Implement Feedback and Non-Authoritative AI Metadata Persistence

Wire the Python backend to receive frontend feedback and persist AI provenance without conflicting with Supabase transcript ownership.

## Endpoint

`POST /api/feedback`

Request fields:
`category, rating, message, route, thread_id, message_id, subject_id, language, app_version`.

Categories: `answer_quality|bug|feature_request|content_gap|other`.
One of `message` or `rating` must be present.

Response:
`feedback_id, created_at`.

## Tasks

1. Refactor `src/feedback.py` so API feedback can be written safely per student (preferred) or with an explicit student identifier in a protected local store. Do not keep all user feedback in one ambiguous shared JSONL if that risks mixing students.
2. Preserve append-only semantics and malformed-line tolerance.
3. Do not log full private prompt/answer content in diagnostics merely because feedback references a message.
4. Add a lightweight AI metadata/provenance store keyed by `student_id + thread_id + python_message_id` containing only fields useful for provenance/history, such as:
   - source IDs/material IDs;
   - used model/provider;
   - retrieval summary;
   - subject/component/language;
   - generation timestamp;
   - optional frontend/Supabase message ID when later supplied.
5. Clearly mark this store non-authoritative for chat transcript. Do not duplicate full Supabase messages unless a later migration explicitly chooses Python transcript ownership.
6. If the current user-memory pipeline needs transcript text, do not secretly treat provenance metadata as transcript. Keep the limitation documented.
7. Add tests for feedback validation, two-user isolation, malformed existing JSONL, safe redaction/logging, and metadata lookup.
8. Return structured filesystem/storage failures through the common API error envelope.

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
