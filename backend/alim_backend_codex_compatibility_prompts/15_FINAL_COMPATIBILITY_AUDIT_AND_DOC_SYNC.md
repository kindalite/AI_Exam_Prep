# Prompt 15 — Final Backend Compatibility Audit and Documentation Sync

Perform a final audit after all previous migration prompts. Do not add unrelated features. The goal is to prove the Python backend is ready for the Lovable frontend integration work.

## Audit against Lovable contract

Verify all of these:

### Runtime
- FastAPI import path is `src.api.main:app`.
- local default listener is `127.0.0.1:8001`.
- `/docs` and `/openapi.json` work.
- Streamlit still runs during the transition.

### Subjects
- exactly 15 top-level API subjects;
- stable IDs match frontend slugs;
- SPF components are nested/validated correctly;
- combined requests can retrieve both component corpora;
- language map is exact.

### Identity/privacy
- API user operations use sanitized `X-Student-Id`;
- local Python login is not required by API;
- no cross-user RAG/file leakage;
- public web privacy defaults preserved.

### Ownership
- Supabase remains authoritative for auth/chat transcript in Stage 1;
- Python does not mutate Lovable grades/planner/profile/localStorage state;
- Python stores AI/practice/feedback/index data only in its own local stores.

### Endpoints
- health/model status;
- subject/detail/goals/materials;
- document import;
- chat JSON and, if completed, SSE;
- quiz/mock exam/study plan/grade/feedback.

### Contract details
- snake_case JSON;
- standard APIError envelope;
- request IDs;
- truthful source snippets;
- correct timeout/error status behaviour;
- exact grade math;
- UTC timestamps;
- model metadata.

## Documentation updates

Update/create:

- `README_RUN_API.md` with exact Conda + Uvicorn commands;
- `.env.example` with API/provider settings but no secrets;
- `docs/API_IMPLEMENTATION_STATUS.md` mapping each Lovable endpoint to Python route/service/tests;
- `docs/LOVABLE_BACKEND_COMPATIBILITY_MATRIX.md` status column;
- existing code handoff docs to state that an HTTP API now exists;
- OpenAPI export: `docs/openapi.json` or `docs/openapi.yaml` generated from the real app;
- troubleshooting for CORS, missing header, model offline, empty index, upload parse failure, remote model unreachable.

## Produce a frontend handoff note

Create `docs/READY_FOR_LOVABLE_FRONTEND.md` containing only the integration facts the frontend team needs:

- base URL;
- API entry points;
- `X-Student-Id` requirement;
- CORS origin;
- mode/health behaviour;
- chat JSON/SSE support status;
- which persistence remains Supabase;
- which endpoints are implemented;
- known limitations, especially conversation history if still single-turn;
- path to generated OpenAPI spec.

## Final verification

Run the full regression ladder. Do not declare compatibility if any required contract test fails. If optional live-model checks cannot run, clearly mark them unverified rather than passing them by assumption.

Return a concise list of:
1. completed compatibility items;
2. remaining frontend work;
3. remaining backend limitations;
4. exact commands to start backend and verify `/health`.

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
