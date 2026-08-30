# Lovable API Test Report

Date: 2026-08-19  
Environment: `/home/kindalite/anaconda3/envs/alim_study_assistant`

## Regression ladder

| Rung | Command | Result |
| --- | --- | --- |
| Compile/import | `python -m py_compile app.py src/*.py src/api/*.py src/api/routes/*.py src/api/schemas/*.py src/services/*.py scripts/api_smoke_test.py scripts/dry_run_lovable_contract.py scripts/system_smoke_fastapi_ollama.py` | PASS |
| Dedicated API contract | `python -m pytest -q tests/api` | **6 passed** |
| Focused domain/API | `python -m pytest -q tests/test_retrieval.py tests/test_services.py tests/test_upload_service.py tests/test_model_providers.py tests/test_api_study_tools.py tests/test_api_feedback_metadata.py tests/test_api_chat_streaming.py` | **24 passed** |
| Full regression | `python -m pytest -q` | **129 passed, 1 skipped**, 3 known Chroma deprecation warnings |
| Existing no-external | `python scripts/dry_run_full_system_no_external.py` | PASS (5 checks) |
| API smoke | `python scripts/api_smoke_test.py` | PASS (health, subjects, docs, OpenAPI) |
| Lovable dry run | `python scripts/dry_run_lovable_contract.py` | PASS (**14 HTTP 200 calls**) |

The Lovable dry run covers health, model status, subject catalogue/detail/goals/materials,
document import, JSON chat, SSE chat, quiz, mock exam, study plan, grading, and feedback.
It uses temporary storage, an in-memory vector store, deterministic fake generation,
and no Lovable, Supabase, Ollama, remote LLM, or public network dependency.

## Opt-in system checks

The following checks were invoked without their opt-in variables and correctly skipped:

- `scripts/smoke_local_ollama.py` — set `RUN_LOCAL_OLLAMA_SMOKE=1`.
- `scripts/smoke_remote_openai_compatible.py` — set `RUN_REMOTE_LLM_SMOKE=1`.
- `scripts/system_smoke_fastapi_ollama.py` — set `RUN_FASTAPI_OLLAMA_SMOKE=1`.

## Verified contract invariants

- All documented method/path pairs and concrete OpenAPI response models exist.
- Core schema properties are `snake_case`; JSON and SSE chat modes are documented.
- Common errors carry `code`, `message`, `detail`, `retryable`, and `request_id`.
- Request IDs, local CORS, 15 top-level subjects, nested SPF components, language rules,
  two-user isolation, exact Swiss-grade math, upload error codes, model 503 behavior,
  UTC timestamps, and JSON/SSE metadata parity are covered across the API suites.

## Remaining intentional Stage-1 limits

- `X-Student-Id` is a sanitized local bridge, not cryptographic authentication.
- Supabase remains authoritative for chat transcripts; Python provenance contains no
  prompt/answer text, and continuity is limited to already indexed student memory.
- Remote OpenAI-compatible vision is not configured; image requests receive an explicit
  capability warning and continue to rely on existing local OCR/description fallbacks.
- Real Ollama and remote-provider checks remain opt-in and were not run in this report.
- Study-plan responses are proposals; planner CRUD/localStorage remains frontend-owned.
