# Prompt 06 — Implement Pydantic Models that Mirror Lovable's Frontend Contract

Create a typed schema layer matching the Lovable handoff exactly. Do not change frontend field names or invent a second wire format.

## Schema package

Create something like:

```text
src/api/schemas/
  __init__.py
  common.py
  subjects.py
  materials.py
  chat.py
  quiz.py
  mock_exam.py
  grading.py
  study_plan.py
  feedback.py
  health.py
```

## Wire conventions

- JSON fields are `snake_case`.
- IDs are strings.
- timestamps are ISO-8601 UTC.
- language values are `de|en|fr`.
- unknown top-level subject IDs are rejected.
- `component_subject_id` is only valid for `spf_biology_chemistry` and must be one of `spf_biology|spf_chemistry`.

## Required models

Implement models matching Lovable's names/fields:

- `SubjectModel`, `SubjectComponentModel`, `LearningGoalModel`
- `MaterialModel`, `MaterialSourceModel`
- `ChatRequest`, `ChatResponse`, `SourceSnippet`, retrieval summary model
- `Quiz`, `QuizQuestion`
- `MockExam`, `MockExamQuestion`
- `GradingRequest`, `GradingResult`
- `StudyPlan`, `StudyPlanItem`
- `FeedbackEntry` + feedback response
- `ModelStatus`, `BackendHealth`
- `APIError`/error detail model

## Critical field details

### ChatRequest
Required: `thread_id`, `subject_id`, `language`, `academic_year`, `grade_level`, `question`.
Optional/defaulted: `component_subject_id`, `learning_goal_id`, `material_ids=[]`, `top_k=6`, `include_sources=true`, `stream=false`.
Validate `question` non-empty and <=4000 chars; validate reasonable `top_k` bounds.

### ChatResponse
`thread_id`, `message_id`, `answer`, `sources`, `exam_tip`, `used_model`, `retrieval_summary`, `language`, `created_at`.

### SourceSnippet
`source_id`, `material_id`, `material_name`, `section`, `page`, `snippet`, `score`, `url`.
Preserve enough source metadata from existing `RetrievedChunk` to populate it; never fake a page or URL.

### Quiz
Questions support `multiple_choice|short_answer|long_answer|true_false` and fields from the frontend model. Include `component_subject_id` even if older frontend examples omit it.

### Grading
`swiss_grade` must represent the **exact** formula result (clamped 1–6), not frontend 0.5 rounding. `rubric_used` is a string list. Preserve source snippets.

### Health/error
Match the documented frontend shapes. Error fields `detail` and `request_id` may be nullable, but the envelope is stable.

## Tasks

1. Implement schema models and validation.
2. Add conversion/adaptation helpers between existing dataclasses (`Subject`, `RetrievedChunk`, `LLMResponse`, etc.) and API models. Keep conversion out of route handlers where nontrivial.
3. Export schema JSON/OpenAPI cleanly without arbitrary `Any` for core contract objects.
4. Add schema tests for valid examples from the Lovable docs and invalid edge cases.
5. Add an OpenAPI snapshot/contract test that verifies endpoint model refs once routes are available.
6. Do not mirror frontend-only localStorage models (`PlannerEvent`, real `Assessment`, etc.) unless an API endpoint actually needs their shape. Avoid overengineering.

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
