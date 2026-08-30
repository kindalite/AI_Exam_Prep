# Final Backend Compatibility Audit

Audit date: 2026-08-19

## Result

The Python backend is ready for Stage-1 Lovable frontend integration. Required
contract checks pass; live model integrations remain explicitly unverified
unless their opt-in smoke variables are enabled.

## Runtime

- FastAPI application: `src.api.main:app`.
- Default command binds `127.0.0.1:8001`; `/docs` and `/openapi.json` pass smoke tests.
- `app.py` remains importable and Streamlit dependencies/tests remain intact.

## Contract and privacy

- Exactly 15 top-level subject IDs; SPF biology/chemistry are validated nested
  components and combined retrieval queries both corpora.
- Subject language enforcement includes CEFR-B1 French instructions.
- User operations require sanitized `X-Student-Id`; upload, files, vector
  collections, memory, practice, feedback, and provenance are isolated.
- Public-web defaults do not send private notes/query text to public search.
- Supabase remains authoritative for API auth context and chat transcripts.
  Python does not mutate Lovable real grades, planner, profile, colours, or
  localStorage state.

## Implemented surface

Health/model status, subject catalogue/detail/goals/materials, document import,
chat JSON/SSE, quiz, mock exam, study-plan proposal, exact AI grading, and
feedback are implemented and represented in `openapi.json`.

Cross-cutting behavior is verified for snake_case, standard errors, request IDs,
CORS, real source metadata, timeouts, upload/media errors, exact unrounded grade
math, UTC timestamps, local/remote model metadata, SSE cleanup, and two-user
isolation.

## Ownership and remaining limits

- `X-Student-Id` is a Stage-1 bridge and must be supplied by the authenticated
  frontend; it is not cryptographic authentication.
- Chat continuity is single-turn plus previously indexed student memory because
  Python receives no Supabase transcript.
- Remote text-only providers return an explicit vision capability warning; local
  OCR/image description remains the fallback path.
- Live Ollama and remote OpenAI-compatible behavior must be verified in the
  target deployment using opt-in smoke scripts.

Evidence: `LOVABLE_API_TEST_REPORT.md`, `API_IMPLEMENTATION_STATUS.md`, and the
committed generated `openapi.json`.
