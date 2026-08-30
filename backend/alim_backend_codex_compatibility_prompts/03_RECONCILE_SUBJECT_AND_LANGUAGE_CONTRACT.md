# Prompt 03 — Reconcile Python Subjects, SPF Components, Languages, and Legacy Storage

Make the Python backend compatible with the Lovable frontend's frozen subject contract while preserving existing backend data/folders where possible.

## Authoritative frontend contract

Exactly 15 top-level subjects:

1. `mathematics` — English
2. `physics` — English
3. `english` — English
4. `history` — English
5. `french` — French B1
6. `german` — German
7. `biology` — German
8. `chemistry` — German
9. `spf_biology_chemistry` — German, virtual combined top-level subject
10. `philosophy` — German
11. `political_education` — German
12. `pedagogics_psychology` — German
13. `economics` — German
14. `art` — German
15. `sport` — German

Component IDs, never top-level subjects:
- `spf_biology`
- `spf_chemistry`

## Rules

- The frontend remains authoritative for card count, display labels, yearly-average combination, and component-average display.
- Python uses stable IDs as corpus/storage/API keys; never derive IDs from display names at runtime.
- For `spf_biology_chemistry` + component ID, use that component corpus only.
- For `spf_biology_chemistry` without a component ID, retrieve/aggregate from both SPF component corpora.
- Reject `spf_biology` or `spf_chemistry` when supplied as top-level `subject_id` to public API validation.
- French outputs must be simple CEFR B1 French; backend must enforce the explicit `language` request field rather than infer from question text.

## Tasks

1. Refactor `src/subject_registry.py` so it has a stable API-facing subject model matching the 15 top-level IDs and virtual SPF combined parent.
2. Preserve existing legacy folders/material where the old registry uses different names. Add an explicit alias/migration map rather than silently renaming/deleting data.
3. Add missing regular subjects/folders: `biology`, `economics`, `art`, `sport`.
4. Represent `spf_biology_chemistry` as a virtual parent with component metadata. Do not create a duplicate combined corpus unless there is a clearly justified need.
5. Keep `spf_biology` and `spf_chemistry` as valid corpus/component keys.
6. Update `src/subject_languages.py` to map API values `de`, `en`, `fr` and produce precise language instructions:
   - German: Grade-11 Swiss Gymnasium register;
   - English: clear academic English at Grade-11 level;
   - French: simple CEFR B1, short sentences/common vocabulary, optional gloss only if needed.
7. Add validation helpers such as:
   - `validate_top_level_subject_id()`
   - `validate_component_for_subject()`
   - `corpus_keys_for_request(subject_id, component_subject_id)`
   - `language_for_api_subject()`
8. Update material routing aliases/tests so existing learning material is still discoverable under the new stable IDs.
9. Ensure setup creates starter subject folders without overwriting existing learning goals/exam criteria.
10. Add tests covering all 15 top-level subjects, both SPF components, invalid component combinations, language mapping, legacy aliases, and combined-corpus routing.
11. Update backend docs describing the previous 12-subject discrepancy as resolved.

## Do not do

- Do not implement frontend grade-combination logic in Python.
- Do not expose SPF component IDs as extra top-level subjects from `GET /api/subjects` later.
- Do not delete old folders in a destructive migration.

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
