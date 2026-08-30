# Prompt 09 — Implement the Stage-1 Non-Streaming Chat/RAG API

Implement `POST /api/chat` with `stream:false` first. This is the most important integration endpoint.

## Stage-1 ownership

- Supabase remains the authoritative writer for chat threads/messages.
- Python must **not** independently persist an authoritative duplicate transcript in this endpoint.
- `thread_id` is a frontend/Supabase correlation ID.
- Python may persist AI metadata/source provenance keyed by its response/correlation ID in a clearly non-authoritative store, but transcript ownership must stay explicit.

## Request contract

Fields:
`thread_id, subject_id, component_subject_id, language, academic_year, grade_level, question, learning_goal_id, material_ids, top_k, include_sources, stream`.

For this prompt, support only `stream:false`; if `stream:true`, return a structured 400/501 stating streaming is not enabled yet rather than silently changing semantics.

## Required RAG behaviour

1. Validate subject/component/language contract.
2. Resolve `StudentContext` from `X-Student-Id`.
3. Determine corpus keys:
   - normal subject → one corpus;
   - SPF + component → that component only;
   - SPF combined without component → both SPF component corpora.
4. Retrieve user-scoped/private material plus approved shared canonical content without cross-user leakage.
5. Apply `material_ids` restriction when provided.
6. Apply/represent `learning_goal_id` scope when supported; if exact filtering is not possible with current metadata, add metadata during indexing rather than pretending.
7. Include exam criteria and learning goals in prompt context using existing source-priority/token-budget logic.
8. Add performance/history memory only from the current student.
9. Optional web/syllabus retrieval must retain existing permission/privacy policy.
10. Enforce the explicit request `language`, including French CEFR-B1 constraint.
11. Call the existing model client/provider through the framework-neutral service layer.
12. Convert retrieved evidence into `SourceSnippet[]`; preserve real page/source/score metadata and do not invent citations.
13. Produce a concise `exam_tip` grounded in the subject/exam criteria when appropriate. If none can be justified, return null.
14. Return `retrieval_summary` with `chunks_considered`, `chunks_used`, and actual collection names.
15. Return model unavailability as HTTP 503 `model_unavailable`, never a 200 with blank text.

## Conversation-history caveat

The Lovable Stage-1 request contract currently sends the current `question` and `thread_id`, not the full Supabase transcript. Do **not** invent access to Supabase from Python. Keep the endpoint correct for single-turn + persisted student memory. Document conversational continuity as a known limitation unless the frontend contract later supplies prior messages or a secure transcript bridge.

## Tasks

1. Implement the chat service and route.
2. Ensure sync Ollama calls do not block the FastAPI event loop; use an appropriate threadpool/async boundary if the underlying client remains synchronous.
3. Generate a stable response `message_id`/AI-result ID. Document that it is a Python response correlation ID unless/until the frontend maps it to the Supabase assistant message ID.
4. Add request timeout/cancellation-aware boundaries where practical.
5. Add fake-LLM/in-memory-store API tests for normal subject, SPF component, SPF combined, each language, material filtering, empty material, model failure, invalid student ID, and no cross-user retrieval.
6. Add one opt-in live Ollama smoke path but do not make normal tests require Ollama.
7. Verify response shape exactly matches the frontend contract.

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
