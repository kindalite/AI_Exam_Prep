# Codex Prompt Pack — Python Backend ↔ Lovable Frontend Compatibility

This prompt pack was derived from both handoff bundles:

- Lovable frontend docs: API expectations, UI→backend mapping, frontend data model, subject/language rules, state/storage ownership, user flows, route map, component tree, local-development plan, integration TODOs, and open backend questions.
- Python backend docs: current Streamlit architecture, module map, data/user flows, storage layout, configuration, tests, dry runs, and explicit API-extraction guidance.

## High-impact mismatches to fix

1. The Python code has no HTTP/FastAPI backend today.
2. The Python subject registry has 12 executable subjects; the frontend contract has 15 top-level subjects plus `spf_biology` and `spf_chemistry` component IDs.
3. The current Streamlit chat calls shared `retrieve_study_context()` rather than the existing user-scoped retrieval path. This must not be exposed as a multi-user API unchanged.
4. Python currently uses local JSON authentication; the frontend uses Supabase auth. For Stage 1, the API should accept a sanitized `X-Student-Id` from the authenticated frontend rather than recreate login/authentication.
5. Chat transcripts remain Supabase-owned in Stage 1. Python should return AI results/metadata without becoming a second transcript authority.
6. Python's existing grading function may apply its own rounding. The API contract requires an exact Swiss grade from `points/max*5+1`, clamped to 1–6; frontend owns 0.5 display rounding and colours.
7. Existing model code is Ollama-specific even though `MODEL_PROVIDER` is configurable. The frontend contract expects model status to represent local/remote providers; add a provider seam without breaking Ollama.

## Recommended execution order

Run these prompts in order, one Codex task/commit at a time:

1. `01_BASELINE_AUDIT_AND_GUARDRAILS.md`
2. `02_EXTRACT_FRAMEWORK_NEUTRAL_SERVICES.md`
3. `03_RECONCILE_SUBJECT_AND_LANGUAGE_CONTRACT.md`
4. `04_ADD_API_IDENTITY_AND_USER_SCOPING.md`
5. `05_BUILD_FASTAPI_FOUNDATION.md`
6. `06_IMPLEMENT_PYDANTIC_CONTRACT_MODELS.md`
7. `07_IMPLEMENT_SUBJECT_GOAL_MATERIAL_READ_APIS.md`
8. `08_IMPLEMENT_DOCUMENT_IMPORT_AND_INDEXING_API.md`
9. `09_IMPLEMENT_CHAT_RAG_API_NON_STREAMING.md`
10. `10_IMPLEMENT_AI_STUDY_TOOL_APIS.md`
11. `11_IMPLEMENT_FEEDBACK_AND_AI_METADATA_PERSISTENCE.md`
12. `12_ADD_MODEL_PROVIDER_ABSTRACTION_AND_REMOTE_GPU_SUPPORT.md`
13. `13_ADD_CHAT_SSE_STREAMING.md`
14. `14_ADD_CONTRACT_TESTS_SMOKE_AND_DRY_RUNS.md`
15. `15_FINAL_COMPATIBILITY_AUDIT_AND_DOC_SYNC.md`

## Important entry-point decision

Do **not** create a Python package named `app/`: this backend already has the Streamlit composition file `app.py`. Create the FastAPI application under:

```text
Code/src/api/main.py
```

and run it as:

```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 8001
```

This avoids an `app.py` / `app` package import collision and lets Streamlit remain available during migration.
