# Prompt 02 — Extract Framework-Neutral Backend Services Without Breaking Streamlit

Refactor the current Python Streamlit monolith so FastAPI can call the same business logic later. **Do not add public HTTP endpoints yet.** Preserve Streamlit behaviour.

## Problem to solve

The handoff notes say `app.py` still directly orchestrates chat, ingestion, study-plan generation, grading, feedback, and stats. FastAPI route handlers must not copy that logic. Create framework-neutral service functions that both Streamlit and the future API can call.

## Tasks

1. Inspect `app.py` and identify direct orchestration for:
   - chat/RAG/model invocation;
   - material discovery/loading/index rebuild;
   - quiz generation;
   - mock exam generation;
   - study plan generation;
   - grading;
   - feedback;
   - model/health checks.
2. Introduce a service layer under a clear namespace, preferably:

```text
src/services/
  __init__.py
  chat_service.py
  subject_service.py
  material_service.py
  quiz_service.py
  mock_exam_service.py
  grading_service.py
  study_plan_service.py
  feedback_service.py
  health_service.py
```

3. Move orchestration, not low-level implementation. Existing modules such as `retrieval.py`, `document_loaders.py`, `llm_client.py`, `prompts.py`, `quiz_generator.py`, etc. remain the implementation building blocks.
4. Services must accept explicit arguments/context rather than reading Streamlit globals/session state.
5. Services must return typed dataclasses or plain framework-neutral result objects. Do not return Streamlit objects or render UI.
6. Preserve dependency-injection seams such as `call_llm`; extend them where useful so unit tests can avoid Ollama.
7. Update Streamlit renderers to call the new services without changing visible behaviour.
8. Do not yet change authentication ownership, subject IDs, or persistence format beyond what is necessary for extraction.
9. Add focused service tests proving existing workflows can execute without importing Streamlit.
10. Add an import-level test that imports every new service module in a minimal environment.

## Acceptance criteria

- Streamlit still starts through `streamlit run app.py`.
- Existing test suite remains green.
- Core AI workflows can now be invoked from Python functions with no `st.session_state` dependency.
- Route handlers can later be thin adapters around these services.

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
