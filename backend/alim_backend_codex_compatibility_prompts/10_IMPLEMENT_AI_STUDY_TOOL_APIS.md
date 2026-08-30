# Prompt 10 — Implement Quiz, Mock Exam, Study Plan, and AI Grading APIs

Expose the existing Python generation/grading intelligence through Lovable-compatible FastAPI endpoints without duplicating logic.

## Endpoints

- `POST /api/quiz/generate`
- `POST /api/mock-exam/generate`
- `POST /api/study-plan/generate`
- `POST /api/grade`

All subject-specific requests must validate `subject_id`, `component_subject_id`, explicit `language`, `academic_year`, and `grade_level` as applicable.

## Quiz

Reuse `quiz_generator.py` / `quiz_mode.py` / prompt and retrieval services. Return structured JSON, not a blob of unparsed model text. Required frontend fields include quiz/question IDs, type, prompt, options/correct index where relevant, expected answer where relevant, points, explanation, learning-goal ID, source references, model, timestamp.

Preserve hidden-solution policy internally. The API response may include answer/explanation only if that is consistent with the frontend's quiz mode; if exposing solutions would violate existing policy, split generation into visible quiz vs protected solution data and document the contract gap rather than weakening the policy.

## Mock exam

Reuse `mock_exam_generator.py` / `exam_mode.py`. Return question points and rubric lines in structured form. Preserve total-point integrity: sum of question points should equal `total_points` or the response should clearly state/normalize it deterministically.

## Study plan

Reuse `study_plan_generator.py`, `performance_tracker.py`, and adaptive helpers. Python proposes plan items only. It must **not** write Lovable planner events. The frontend reviews and then stores generated events in localStorage.

Use available exam dates, time slots, weak-topic/performance context, learning goals, and max daily minutes. Return dates/times in the documented formats and ensure no overlapping items within the proposed slots.

## Grading

Reuse grading prompt/evidence logic but satisfy the frontend rule:

```text
exact_grade = 1 + 5 * points_awarded / max_points
```

clamped to `[1.0, 6.0]` and **not rounded to 0.5 by the API**.

If existing `grader.calculate_grade` rounds, preserve it for legacy Streamlit if needed and introduce a separate exact API calculation/helper so existing behaviour/tests are not silently broken.

Return:
`points_awarded, max_points, swiss_grade, grade_formula, strengths, missing_points, improvement_advice, rubric_used, sources, graded_at, used_model`.

Use the subject's exam criteria and, where given, generated-exam rubric. Do not invent criteria unavailable from files/request.

## Persistence

Reuse existing per-user `practice_store`, attempt/report storage, and performance tracker where sensible. Keep AI practice distinct from the Lovable user's real grades. Do not modify frontend grade averages. Persist generated practice/history in Python for future history endpoints, but do not require those endpoints in Stage 1.

## Tasks

1. Add/finish service-layer functions returning structured typed results.
2. If existing LLM outputs are free-form text, add robust parsing/validation with one constrained repair/retry path, then fail with a structured error rather than returning malformed JSON.
3. Apply token budget and RAG source priority consistently with chat.
4. Ensure each operation is user-scoped.
5. Add timeout handling up to the frontend's 120-second expectation; do not leave endless requests.
6. Add tests with fake LLM outputs for valid/malformed JSON, missing material, all languages, SPF routing, exact grade math, rubric grounding, hidden-solution invariants, plan slot validity, and persistence isolation.
7. Add dry-run coverage for all four endpoints without Ollama/network.

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
