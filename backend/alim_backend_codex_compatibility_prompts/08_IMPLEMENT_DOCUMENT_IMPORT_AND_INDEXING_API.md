# Prompt 08 — Implement `POST /api/import/document` and Safe User-Scoped Indexing

Connect Lovable's MaterialsPanel/TranscriptImport flow to the existing Python document ingestion pipeline.

## Contract

`POST /api/import/document`

Content type: `multipart/form-data`.
Fields:
- `file`
- `subject_id`
- `component_subject_id` (optional/required for SPF component upload as applicable)
- `section`
- `language`

Supported frontend-targeted types: PDF, DOCX, MD, TXT, PNG, JPEG, SVG where the existing backend safely supports them.

Response fields:
`material_id, name, type, section, language, pages, chunks_indexed, status, warnings, added_at`.

Errors:
- 413 `file_too_large`
- 415 `unsupported_media_type`
- 422 `parse_failed`
- 409 `index_busy` where concurrent rebuild would be unsafe

## Critical backend realities

- Existing loaders already support document/multimodal parsing and graceful warnings.
- Existing `build_subject_index()` rebuilds a collection; manifest helpers exist but are not the primary incremental path.
- Uploaded student material must not be placed into a shared collection that another student can query.

## Tasks

1. Add a safe upload service that streams/copies the upload to a temporary file with a configured size limit; do not read arbitrary unlimited uploads into memory.
2. Validate extension/MIME conservatively. Never execute document contents/macros/scripts.
3. Store accepted user uploads under the sanitized per-user subject directory and preserve original display name separately from filesystem-safe name.
4. Generate a stable `material_id` and persist metadata sufficient for future filtering/retrieval.
5. Parse with existing `load_document`/multimodal helpers. Preserve partial text and warnings when optional OCR/vision dependencies are missing.
6. Index into the **user-scoped** subject/component corpus. Do not rebuild another user's collection.
7. If current indexing APIs only support full rebuild, implement safe per-user rebuild orchestration with an operation lock/state to prevent concurrent corruption. Do not silently claim incremental indexing.
8. For `spf_biology_chemistry`, require/resolve a component for uploads unless the file is explicitly a shared combined/canonical resource. Do not duplicate private material into both components by default.
9. Return truthfully computed `pages`/`chunks_indexed`; use null/omission where the loader cannot know.
10. On parse failure, preserve a metadata record with `Needs review` where feasible so the frontend can display it, but do not put broken content into Chroma.
11. Add tests with small fixture files for MD/TXT/DOCX/PDF if available, invalid extension, oversized file simulation, malformed file, missing optional OCR, concurrent/busy indexing, and user isolation.
12. Add a dry-run script that ingests a temporary sample file into an in-memory/fake store and prints the API-shaped result.

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
