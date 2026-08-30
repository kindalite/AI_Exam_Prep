# Prompt 05 — Build the FastAPI Foundation Beside Streamlit

Add a real local HTTP backend without breaking the existing Streamlit entry point.

## Entry point

Because `Code/app.py` already exists, do **not** create an `app/` package. Create:

```text
src/api/
  __init__.py
  main.py
  dependencies.py
  errors.py
  middleware.py
  routes/
    __init__.py
    health.py
    subjects.py
    materials.py
    chat.py
    study_tools.py
    feedback.py
```

Run with:

```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 8001
```

## Tasks

1. Add compatible pinned dependencies to `environment.yml`/requirements following the repo's existing versioning policy:
   - FastAPI;
   - Uvicorn;
   - `python-multipart` for uploads;
   - HTTP/TestClient dependency if not already present.
2. Create the FastAPI application with title/version metadata and a lifespan/startup timestamp.
3. Configure CORS exactly for local frontend integration:
   - origins: `http://localhost:8080`, `http://127.0.0.1:8080`;
   - methods: `GET`, `POST`, `OPTIONS`;
   - request headers: `Content-Type`, `Authorization`, `X-Student-Id`, `X-Request-Id`;
   - expose `X-Request-Id`.
4. Add request-ID middleware:
   - accept a valid incoming `X-Request-Id` or generate one;
   - attach it to request state;
   - emit it on every response;
   - include it in structured error envelopes.
5. Implement the standard error envelope exactly:

```json
{
  "error": {
    "code": "subject_not_found",
    "message": "...",
    "detail": "...",
    "retryable": false,
    "request_id": "req_..."
  }
}
```

6. Add exception handlers for validation, known domain errors, model/vector unavailability, file/media errors, and unexpected internal errors. Do not leak tracebacks/secrets to clients.
7. Add `GET /health` and `GET /api/model/status` as the first real routes, backed by existing model/vector/dependency helpers rather than hardcoded health.
8. `GET /health` should return as available:
   - `status` (`ok|degraded|error`);
   - API version;
   - uptime;
   - vector store type/reachability/collection count;
   - model server reachability/provider;
   - count of indexed top-level subjects;
   - UTC `checked_at`.
9. `GET /api/model/status` should return:
   - provider;
   - model;
   - safe endpoint/base URL;
   - mode `local|remote`;
   - reachable;
   - latency if measurable;
   - embedding model;
   - optional fallback provider.
10. Health/status endpoints must not require `X-Student-Id`.
11. Add `src/api/dependencies.py` with reusable FastAPI dependencies for config, student context, services, and request ID. Avoid global mutable service state where tests need injection.
12. Add API startup smoke tests using FastAPI TestClient with no live model/network requirement.
13. Update local-run documentation to use `uvicorn src.api.main:app ...` instead of the frontend handoff's provisional `app.main:app` command.

## Acceptance criteria

- `curl http://localhost:8001/health` returns the documented shape.
- Swagger is available at `/docs`, OpenAPI at `/openapi.json`.
- Streamlit still runs independently.
- API can be imported/tested without starting Ollama.

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
