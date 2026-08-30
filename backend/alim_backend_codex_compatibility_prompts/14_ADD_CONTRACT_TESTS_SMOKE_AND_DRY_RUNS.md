# Prompt 14 — Add Lovable Contract Tests, API Smoke Tests, and No-External Dry Runs

Build a verification layer proving the Python API is compatible with the Lovable handoff while preserving the mature existing Python test suite.

## Test architecture

Create dedicated API tests, e.g.:

```text
tests/api/
  test_health_api.py
  test_subjects_api.py
  test_materials_api.py
  test_chat_api.py
  test_quiz_api.py
  test_mock_exam_api.py
  test_grading_api.py
  test_study_plan_api.py
  test_feedback_api.py
  test_errors_and_cors.py
  test_openapi_contract.py
  test_user_isolation_api.py
```

Use FastAPI TestClient/httpx, temporary roots, fake LLM providers, in-memory vector stores/deterministic embeddings where possible.

## Contract assertions

1. Every documented endpoint exists with correct method/path.
2. Wire field names remain `snake_case`.
3. Standard error envelope is used for all non-2xx domain/validation failures where FastAPI customization permits.
4. `X-Request-Id` is returned.
5. CORS accepts `http://localhost:8080` and required headers.
6. 15 top-level subjects are returned; SPF components are nested, never top-level.
7. Languages are enforced, including French B1 prompt constraint.
8. User-scoped material/RAG is isolated between two students.
9. Exact Swiss API grade uses `1 + 5*achieved/max`, while legacy/frontend rounding remains separate.
10. Model unavailable is HTTP 503 with `model_unavailable`.
11. Upload errors map to 413/415/422 contract codes.
12. Chat JSON response and SSE final event use compatible metadata.
13. All timestamps are valid ISO-8601 UTC.

## Dry-run/smoke scripts

Add scripts such as:

- `scripts/api_smoke_test.py` — starts/invokes app in-process, checks health and basic routes.
- `scripts/dry_run_lovable_contract.py` — exercises all endpoints with fakes and prints a concise compatibility report.
- `scripts/system_smoke_fastapi_ollama.py` — opt-in real model integration.

Do not require live Lovable/Supabase for backend contract tests.

## Regression ladder

Run, in order:

1. compile/import checks;
2. focused `tests/api`;
3. existing focused domain tests;
4. full `pytest -q`;
5. existing no-external dry run;
6. new Lovable-contract dry run;
7. optional real Ollama smoke if available.

## Deliverable

Write `docs/LOVABLE_API_TEST_REPORT.md` with commands, pass/fail counts, skipped optional-system checks, and any remaining contract gaps.

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
