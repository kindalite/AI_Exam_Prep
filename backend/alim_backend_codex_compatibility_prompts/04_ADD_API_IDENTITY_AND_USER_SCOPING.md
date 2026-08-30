# Prompt 04 — Add the Stage-1 Identity Bridge and Make API RAG User-Scoped

Prepare the backend for an authenticated Lovable frontend without replacing Supabase auth.

## Context

The Python app currently has local username/password auth and per-user filesystem helpers. Lovable uses Supabase authentication. The Stage-1 integration decision is:

- Supabase stays the authentication authority.
- The local browser sends `X-Student-Id` (the Supabase user ID) to FastAPI.
- Because FastAPI is bound to `127.0.0.1`, the backend does not verify a Supabase JWT in Stage 1.
- Every user-specific path/collection must still be sanitized/scoped.

The current Streamlit chat uses shared `retrieve_study_context()`, while user-scoped retrieval helpers already exist. Do not expose the shared path as private-user RAG.

## Tasks

1. Add a framework-neutral identity/context object, e.g. `StudentContext`, containing at minimum a sanitized `student_id` and optionally request/correlation metadata.
2. Reuse `user_data_paths.py` sanitization and collection-name helpers. Do not concatenate raw `X-Student-Id` into paths or Chroma names.
3. Add a single helper for resolving API student identity from a string. FastAPI wiring will use it later.
4. Introduce an API-safe retrieval orchestration function that:
   - scopes user uploads/notes/history to the current student;
   - can also include approved shared non-private subject sources such as canonical exam criteria/syllabus;
   - never retrieves another student's collection;
   - supports one or both SPF component corpora according to the subject contract;
   - supports optional `material_ids` and `learning_goal_id` filters where existing metadata allows it;
   - preserves source metadata for citations.
5. Reuse `build_user_subject_index`, `retrieve_for_user_subject`, and `rag_memory_indexer.py` where appropriate rather than reinventing collection naming.
6. If current user-scoped indexing cannot include both shared and user material cleanly, implement a layered result merge with explicit source layers instead of copying private content into a shared collection.
7. Decide and document how canonical shared sources and per-user uploads are prioritized, consistent with current prompt priority: current request → user/teacher local material → learning goals/exam criteria → syllabus → performance/history → optional web.
8. Do not make the API depend on the Python local-auth database. Keep local auth available only for the legacy Streamlit app.
9. Add tests with two synthetic student IDs proving:
   - collections/paths differ;
   - student A cannot retrieve student B material;
   - shared canonical content may be visible to both;
   - SPF component scoping is respected;
   - malformed/raw IDs cannot escape the configured user root.
10. Add a configurable developer-only fallback student ID if needed for tests/manual development, but default production-local behaviour should require `X-Student-Id` for user-scoped AI/material operations.

## Acceptance criteria

Before FastAPI routes are added, a service call with `StudentContext('A')` must be provably isolated from `StudentContext('B')`.

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
