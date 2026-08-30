# Prompt 01 — Baseline Audit, Compatibility Matrix, and Guardrails

You are modifying the existing Python backend for **Alim's Study Assistant** so it can serve the separate Lovable/TanStack Start frontend. Do not implement the API yet. First establish a verified baseline and a concrete migration matrix.

## Read before editing

Read the Python code and its handoff docs, especially:
- `app.py`
- `src/config.py`
- `src/subject_registry.py`
- `src/subject_languages.py`
- `src/retrieval.py`
- `src/user_data_paths.py`
- `src/chat_history_store.py`
- `src/practice_store.py`
- `src/llm_client.py`
- `src/model_runtime.py`
- `src/prompts.py`
- `src/quiz_generator.py`
- `src/mock_exam_generator.py`
- `src/study_plan_generator.py`
- `src/grader.py`
- `src/feedback.py`
- tests and dry-run scripts

Also read the Lovable handoff documents if they are available in the workspace. The binding target is the API described by `API_EXPECTATIONS.md`, `FRONTEND_DATA_MODEL.md`, `UI_BACKEND_MAPPING.md`, and `SUBJECT_MODEL_AND_LANGUAGE_RULES.md`.

## Tasks

1. Create `docs/LOVABLE_BACKEND_COMPATIBILITY_MATRIX.md` in the Python repository.
2. For every target endpoint, record:
   - frontend action/component;
   - target request schema;
   - target response schema;
   - existing Python functions/modules that can satisfy it;
   - missing orchestration;
   - persistence owner;
   - identity/user-scoping requirement;
   - error/timeout considerations;
   - implementation status.
3. Include at minimum:
   - `GET /health`
   - `GET /api/model/status`
   - `GET /api/subjects`
   - `GET /api/subjects/{subject_id}`
   - `GET /api/subjects/{subject_id}/learning-goals`
   - `GET /api/subjects/{subject_id}/materials`
   - `POST /api/import/document`
   - `POST /api/chat`
   - `POST /api/quiz/generate`
   - `POST /api/mock-exam/generate`
   - `POST /api/study-plan/generate`
   - `POST /api/grade`
   - `POST /api/feedback`
4. Identify every current Streamlit-specific dependency inside business workflows. Mark code that must be extracted into framework-neutral services before FastAPI handlers can reuse it.
5. Explicitly document the current subject mismatch: executable Python registry vs Lovable's 15 top-level IDs and the two SPF component IDs.
6. Explicitly document the current RAG privacy mismatch: Streamlit chat uses shared retrieval even though user-scoped indexing/retrieval exists.
7. Explicitly document ownership boundaries:
   - Supabase owns auth and chat transcript in Stage 1;
   - frontend/localStorage owns real grades, planner, profile, static 15-subject UI list, grade display rounding;
   - Python owns AI/RAG/indexed materials/learning goals/grading evaluation/feedback.
8. Run and record a baseline verification ladder. Use commands appropriate to this repo, e.g. compile, focused tests, `pytest -q`, core dry run. Do not require the live model for the baseline unless available.
9. Create a short `docs/API_MIGRATION_GUARDRAILS.md` listing invariants Codex must preserve in later prompts.
10. Make no behavioural changes except documentation or tiny test-only fixes required to obtain a reproducible baseline.

## Deliverable

Return:
- files created/changed;
- baseline test results;
- high-risk incompatibilities;
- a one-paragraph recommendation on where service extraction should start.

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
