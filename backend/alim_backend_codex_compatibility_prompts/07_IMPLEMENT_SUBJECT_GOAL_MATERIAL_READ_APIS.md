# Prompt 07 — Implement Subject, Learning-Goal, and Material Read APIs

Implement the read endpoints the Lovable School dashboard and MaterialsPanel need. These endpoints enrich the frontend; they must not redefine the frontend's 15-card list or grade state.

## Endpoints

- `GET /api/subjects`
- `GET /api/subjects/{subject_id}`
- `GET /api/subjects/{subject_id}/learning-goals`
- `GET /api/subjects/{subject_id}/materials`

## Behaviour

### `GET /api/subjects`
Return exactly 15 top-level entries in the frozen stable-ID order. SPF components appear only inside the combined subject's `components` list. Return index metadata (`indexed_materials`, `learning_goal_count`, `last_indexed_at`) when available. Never invent frontend grade data.

### `GET /api/subjects/{subject_id}`
Return corpus/index details. For `spf_biology_chemistry` without component selection, aggregate counts/topics over both component corpora without creating a duplicate combined collection.

### Learning goals
Support optional `component_subject_id` and `topic`. Load user-specific goals if the backend's per-user layout contains them; otherwise use approved shared starter/canonical files. Preserve source material references when known. Return read-only data.

### Materials
Support `component_subject_id`, `section`, `include_archived`. Convert existing manifest/loader metadata into frontend material objects. Backend items should represent indexable files/corpus records only; do not try to read Lovable localStorage materials.

## Identity/scoping

- Subject metadata can be public/local and may omit `X-Student-Id` if no private data is included.
- Learning goals/materials that include per-user uploads must use `X-Student-Id` and never expose another user's files.
- Decide endpoint behaviour when no student ID is supplied: either canonical/shared-only view or a documented 400 for private views. Implement consistently and test it.

## Tasks

1. Implement service functions for index counts, last-indexed timestamps, topics, goals, and material inventory.
2. Where the backend currently lacks incremental manifest use, do not pretend index status is more precise than it is. Derive truthful status from existing stores/manifests/collections.
3. Map supported backend formats to frontend material types: PDF, DOCX, PNG, JPEG, SVG, MD, TXT. Preserve warnings/unknown values safely.
4. Return 404 `subject_not_found` for unknown IDs using the standard envelope.
5. For invalid SPF component combinations, return 422/400 with a useful structured message.
6. Add tests for all subject IDs, SPF aggregation, French/German/English language metadata, empty corpus, shared-only mode, and two-user material isolation.
7. Ensure routes are thin; heavy filesystem/Chroma inspection lives in services.

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
