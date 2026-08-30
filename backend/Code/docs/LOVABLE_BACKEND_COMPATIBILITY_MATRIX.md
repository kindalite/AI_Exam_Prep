# Lovable Backend Compatibility Matrix

## Scope and contract status

This document began as the Stage 1 baseline and now records the implemented
FastAPI compatibility layer for the separate Lovable/TanStack frontend.
Streamlit remains available in parallel during the transition.

The named frontend handoff files (`API_EXPECTATIONS.md`,
`FRONTEND_DATA_MODEL.md`, `UI_BACKEND_MAPPING.md`, and
`SUBJECT_MODEL_AND_LANGUAGE_RULES.md`) are not present in this workspace. The
schemas below are therefore a migration shape inferred from the prompt pack
and current Python interfaces. They are deliberately marked **proposed** until
the Pydantic-contract stage freezes exact fields. All public JSON uses
`snake_case`.

Common proposed conventions:

- Requests that touch user material require `X-Student-Id`; the value must be
  sanitized with `sanitize_username()` before it reaches a path or collection
  name.
- Success responses include structured data rather than rendered Markdown or
  Streamlit state. AI text may remain Markdown inside a string field.
- Sources use a shared shape such as `source_id`, `source_name`,
  `source_layer`, `page_number`, `modality`, and `url`.
- Errors use a stable envelope such as `error.code`, `error.message`, and an
  optional `request_id`/`details`; handlers must not expose local paths or
  private source text.
- Slow AI/indexing operations require explicit server-side timeouts and
  cancellation handling. Optional OCR, image, audio, web, and vector failures
  remain warnings where a useful partial result is possible.

## Endpoint matrix

### `GET /health`

| Concern | Baseline / target |
| --- | --- |
| Frontend action | Local-development connectivity check and global backend availability indicator. |
| Request | No body and no student identity. |
| Response (proposed) | `{status, service, version?}` with HTTP 200 when the API process is alive. This must not require Ollama. |
| Existing Python | `load_config()` and import/smoke checks provide building blocks; no HTTP health service exists. |
| Missing orchestration | FastAPI app, health service, request ID/error middleware. |
| Persistence owner | None. |
| Identity/scoping | Public local health check; never echo headers. |
| Errors/timeouts | Must be fast and independent of model/vector/network health. |
| Status | **Implemented and contract-tested** (`src.api.routes.health`). |

### `GET /api/model/status`

| Concern | Baseline / target |
| --- | --- |
| Frontend action | Model readiness/status badge before AI actions. |
| Request | No body; identity not required for provider-level health. |
| Response (proposed) | `{provider, model, status, ready, server_reachable, model_available, message}`. |
| Existing Python | `model_runtime.verify_model_runtime()` returns Ollama-specific `ModelRuntimeStatus`; `ollama_model_manager` performs reachability/model checks. |
| Missing orchestration | Provider-neutral status service and serialization; currently only Ollama is implemented even though `MODEL_PROVIDER` exists. |
| Persistence owner | Python configuration/runtime. |
| Identity/scoping | No student data. Do not return credentials or sensitive provider URLs. |
| Errors/timeouts | Short provider probe; unavailable provider should return structured degraded status rather than crash the API. |
| Status | **Implemented and contract-tested** for Ollama and OpenAI-compatible/vLLM. |

### `GET /api/subjects`

| Concern | Baseline / target |
| --- | --- |
| Frontend action | Populate/validate the frontend subject catalogue and component metadata. |
| Request | No body. Optional identity may be accepted later only for per-user index counts. |
| Response (proposed) | `{subjects: [{subject_id, display_name, language, is_virtual, components, capabilities, indexed_materials?, learning_goal_count?, last_indexed_at?}]}` with exactly 15 top-level subjects; SPF components are nested, not top-level. |
| Existing Python | `subject_registry.build_subject_registry()`, `subjects_for_display()`, and `subject_languages.language_for_subject()`. |
| Missing orchestration | Per-user index metadata aggregation and the HTTP adapter. The stable 15-subject model, legacy aliases, and virtual SPF routing now exist. |
| Persistence owner | Frontend owns its static 15-card display model; Python owns executable corpus/capability metadata. |
| Identity/scoping | Any material/index counts must be derived only from the identified student's scope. Static catalogue data is identity-free. |
| Errors/timeouts | Invalid registry configuration should be a startup/contract failure, not a partial anonymous list. |
| Status | **Implemented and contract-tested** with exactly 15 top-level subjects. |

### `GET /api/subjects/{subject_id}`

| Concern | Baseline / target |
| --- | --- |
| Frontend action | Open a subject dashboard and discover backend capabilities/corpus state. |
| Request | Path `subject_id`; optional SPF `component_subject_id` according to the final contract. |
| Response (proposed) | `{subject_id, display_name, language, instructions, is_virtual, components, capabilities, corpus}`. Do not return frontend-owned grades/planner data. |
| Existing Python | `get_subject()`, `Subject`, learning-goal/criteria paths, collection naming. |
| Missing orchestration | API subject resolution, virtual-parent aggregation, safe not-found mapping, user-specific corpus metadata. |
| Persistence owner | Python for corpus/index details; frontend for profile, grades, planner, colours, labels. |
| Identity/scoping | `X-Student-Id` required if response includes private corpus state. |
| Errors/timeouts | Unknown/invalid subject or invalid SPF component: 4xx structured error. Metadata reads should be fast. |
| Status | **Implemented and contract-tested** with scoped corpus metadata. |

### `GET /api/subjects/{subject_id}/learning-goals`

| Concern | Baseline / target |
| --- | --- |
| Frontend action | Show goals and use a selected goal for chat/quiz/study tools. |
| Request | Path `subject_id`; optional valid component selector for the combined SPF subject. |
| Response (proposed) | `{subject_id, component_subject_id?, learning_goals: [{id, text}], source_updated_at?}`. |
| Existing Python | `retrieval.load_learning_goals()` reads one Markdown file. |
| Missing orchestration | Framework-neutral parser/service, stable goal IDs, per-user/shared ownership resolution, combined-SPF aggregation. |
| Persistence owner | Python owns learning goals. |
| Identity/scoping | Require `X-Student-Id` when goals can come from the user's subject tree. |
| Errors/timeouts | Missing file should normally return an empty list/warning; invalid subject/component is 4xx. |
| Status | **Implemented and contract-tested** with stable goal IDs. |

### `GET /api/subjects/{subject_id}/materials`

| Concern | Baseline / target |
| --- | --- |
| Frontend action | List uploaded/indexed source material and indexing state. |
| Request | Path `subject_id`; optional valid SPF component selector. |
| Response (proposed) | `{subject_id, component_subject_id?, materials: [{material_id, file_name, media_type, status, source_layer, indexed_at?, warning?}], totals}`. |
| Existing Python | `material_router`, `document_loaders`, subject/user folders, Chroma collection names; `material_manifest` has change primitives. |
| Missing orchestration | Safe metadata-only listing, user-root resolution, manifest/index-status service, virtual-parent aggregation. |
| Persistence owner | Python owns uploaded/indexed material and index metadata. |
| Identity/scoping | `X-Student-Id` required; never list another user's files or reveal absolute paths. |
| Errors/timeouts | Listing must not parse documents or initialize large models; corrupt metadata degrades per item. |
| Status | **Implemented and contract-tested** with canonical/user isolation. |

### `POST /api/import/document`

| Concern | Baseline / target |
| --- | --- |
| Frontend action | Upload course material and trigger parsing/indexing. |
| Request (proposed) | Multipart `file`, `subject_id`, optional `component_subject_id`; explicit index/rebuild option only if the frozen contract requires it. |
| Response (proposed) | `{material_id, file_name, subject_id, component_subject_id?, status, chunks_indexed, sources, warnings}`. |
| Existing Python | Streamlit `_save_uploaded_file()`, `save_chat_media()`, `load_document()`, `build_user_subject_index()`, `build_subject_index()`, OCR/multimodal safe wrappers. |
| Missing orchestration | Neutral upload validation/storage service, filename/content limits, atomic write, user-scoped incremental/rebuild policy, index job/result reporting. |
| Persistence owner | Python owns uploaded material and indexes. |
| Identity/scoping | `X-Student-Id` mandatory; sanitize before path/collection use. Uploads must go to the user's subject corpus, not shared folders. |
| Errors/timeouts | Reject unsupported/empty/oversized files; protect against traversal; bound parsing/indexing; preserve warnings for optional tools; avoid leaving ambiguous partial state. |
| Status | **Implemented and contract-tested** with bounded streaming upload and user indexing. |

### `POST /api/chat`

| Concern | Baseline / target |
| --- | --- |
| Frontend action | Submit a subject chat message and render AI answer/source metadata. Supabase continues to store the transcript. |
| Request (proposed) | `{subject_id, component_subject_id?, message, language?, use_syllabus, use_web, attachments?}`. Subject rules determine/validate language. |
| Response (proposed) | `{answer, subject_id, component_subject_id?, language, sources, warnings, model, request_id?}`. No authoritative Python transcript ID is required in Stage 1. |
| Existing Python | `app.render_chat()` orchestrates OCR/audio, `retrieve_study_context()`, prompt construction, `generate_response()`, attempts, and local chat storage. User-scoped `retrieve_for_user_subject()` exists separately. |
| Missing orchestration | Neutral chat service, user-scoped layered retrieval, attachment contract, dependency injection, metadata mapping, and removal of mandatory Python transcript writes. |
| Persistence owner | Supabase owns auth and chat transcript. Python owns inference, RAG, indexed sources, and returned AI metadata; it must not become a second transcript authority. |
| Identity/scoping | `X-Student-Id` mandatory. Current shared retrieval path is not acceptable for multi-user API use. |
| Errors/timeouts | Model timeout/cancellation, empty input validation, optional-tool warnings, safe web-permission enforcement, source redaction. |
| Status | **Implemented and contract-tested** in JSON and SSE modes without transcript ownership. |

### `POST /api/quiz/generate`

| Concern | Baseline / target |
| --- | --- |
| Frontend action | Generate practice questions for a topic/learning goal. |
| Request (proposed) | `{subject_id, component_subject_id?, learning_goal?, topic?, difficulty, question_count?}`. |
| Response (proposed) | `{quiz_id?, subject_id, difficulty_used, questions, sources, warnings, model}`; solutions must remain hidden until allowed by the frontend flow/contract. |
| Existing Python | `create_quiz()`, adaptive-learning helpers, prompts, `timed_practice`, `practice_store`. |
| Missing orchestration | User-scoped retrieval/config injection, structured model-output parsing, contract-safe hidden solutions, thin API adapter. |
| Persistence owner | Python owns AI generation, generated practice metadata, and hidden-solution policy. Frontend owns display/session UI. |
| Identity/scoping | `X-Student-Id` mandatory for private context and persisted generated artifacts. |
| Errors/timeouts | Validate difficulty/count; model timeout/invalid output; no solution leakage on partial/error responses. |
| Status | **Implemented and contract-tested** with structured output and protected solutions. |

### `POST /api/mock-exam/generate`

| Concern | Baseline / target |
| --- | --- |
| Frontend action | Generate an exam-style paper and marking assets. |
| Request (proposed) | `{subject_id, component_subject_id?, total_points, difficulty, topics?, learning_goal_ids?}`. |
| Response (proposed) | `{mock_exam_id?, subject_id, difficulty_used, total_points, questions, sources, warnings, model}` with solutions stored/returned only under the hidden-solution contract. |
| Existing Python | `create_mock_exam()`, adaptive context, prompt builder, `timed_practice`, `practice_store`. |
| Missing orchestration | Same service/config/user-scoping and structured-output work as quiz generation; exact point-total validation. |
| Persistence owner | Python owns generation, criteria, and hidden solutions. |
| Identity/scoping | `X-Student-Id` mandatory for private context/persistence. |
| Errors/timeouts | Validate positive points; model timeout/invalid structure; never reveal hidden solutions early. |
| Status | **Implemented and contract-tested** with normalized points and protected answers. |

### `POST /api/study-plan/generate`

| Concern | Baseline / target |
| --- | --- |
| Frontend action | Request an AI study-plan proposal that the frontend may display/use. |
| Request (proposed) | `{subject_id, component_subject_id?, exam_date, hours_per_week, weak_topics}`. |
| Response (proposed) | `{subject_id, plan, sources, warnings, model}`; it is a proposal, not planner CRUD state. |
| Existing Python | `create_study_plan()`, prompt builder, learning-goal and shared retrieval helpers. |
| Missing orchestration | User-scoped neutral service, date/hour validation, structured plan parsing, injected config/model/retrieval. |
| Persistence owner | Python owns AI proposals; frontend/localStorage owns planner records and CRUD. |
| Identity/scoping | `X-Student-Id` mandatory when private context is used. |
| Errors/timeouts | Reject invalid/past dates according to frozen contract and non-positive hours; model timeout/invalid output. |
| Status | **Implemented and contract-tested** as a non-overlapping proposal only. |

### `POST /api/grade`

| Concern | Baseline / target |
| --- | --- |
| Frontend action | Obtain AI evaluation, points, exact Swiss grade, strengths, weaknesses, and improved answer. |
| Request (proposed) | `{subject_id, component_subject_id?, question, student_answer, maximum_points, marking_scheme?}`. If points are supplied externally, they must be validated against `maximum_points`. |
| Response (proposed) | `{points_achieved, maximum_points, grade_exact, feedback, strengths, weaknesses, improved_answer, sources, warnings, model}`. |
| Existing Python | `create_grading_feedback()`, `calculate_grade()`, `store_grading_attempt()`. Current formula returns a value rounded to two decimals. |
| Missing orchestration | Structured extraction of model-awarded points, exact clamped API-grade calculation without display rounding, per-user persistence decision, user-scoped retrieval. |
| Persistence owner | Python owns AI evaluation and grading computation. Frontend owns real grades, averages, colours, and 0.5 display rounding. |
| Identity/scoping | `X-Student-Id` mandatory when sources/evaluation metadata are user-scoped or persisted. |
| Errors/timeouts | `maximum_points > 0`; points in range; model timeout/invalid evaluation; distinguish exact grade from display grade. |
| Status | **Implemented and contract-tested** with exact unrounded API grade math. |

### `POST /api/feedback`

| Concern | Baseline / target |
| --- | --- |
| Frontend action | Submit rating/comment about an AI feature/result. |
| Request (proposed) | `{subject_id, feature, user_task, app_answer?, rating, comment?, source_chunk_ids?, ai_request_id?}`. |
| Response (proposed) | `{feedback_id, accepted, created_at}` without echoing unnecessary private content. |
| Existing Python | `feedback.save_feedback()` appends shared JSONL and `read_feedback()` reads it. |
| Missing orchestration | User-scoped record/service, validation, stable ID, linkage to AI metadata/request, safe serialization. |
| Persistence owner | Python owns feedback persistence and AI metadata. |
| Identity/scoping | `X-Student-Id` mandatory; current default feedback file is shared and records no user ID. |
| Errors/timeouts | Validate rating range/feature/lengths; append atomically; avoid leaking full prompts/answers in logs or errors. |
| Status | **Implemented and contract-tested** with isolated append-only feedback/provenance. |

## Streamlit-specific workflow dependencies to extract

| Current location | Streamlit coupling / embedded workflow | Required neutral service boundary |
| --- | --- | --- |
| `app._selected_subject()` | Sidebar selection, config load, language derivation. | Subject-resolution/catalogue service with explicit config and IDs. |
| `app._save_uploaded_file()` / `render_ingestion()` | `UploadedFile`, buttons, spinners, shared subject path writes, discovery, syllabus fetch, and index rebuild are interleaved. | Validated user-scoped document import/index service returning metadata and warnings. |
| `app.render_chat()` | File upload, per-user media writes, OCR/vision/audio, shared retrieval, prompt build, model call, performance write, transcript write, and rendering are one function. | Chat orchestration service with injected retrieval/model/media tools; API must use user-scoped retrieval and must not author Supabase transcripts. |
| `app.render_learning_goals()` | Text widgets and shared retrieval are mixed with file reads. | Learning-goal read/parse service and user-scoped related-material query service. |
| `app.render_quiz()` / `render_mock_exam()` / focused `ui_practice_modes` | Widgets invoke generators and timed persistence directly. | Quiz/exam generation services with explicit user/config/retrieval/model dependencies and hidden-solution result types. |
| `app.render_study_plan()` | Widget values call a generator that uses implicit global config/shared retrieval. | Study-plan service with validated inputs and injected dependencies. |
| `app.render_grader()` | Formula, model feedback, manual persistence, and UI state are mixed. | Grading/evaluation service returning exact grade and optional explicitly user-scoped persistence. |
| `app.render_feedback()` | Widget fields write to a shared default file. | Validated user-scoped feedback/AI-metadata service. |
| `app.render_model_runtime_panel()` | Status/warm actions are rendered directly and are Ollama-specific. | Provider-neutral runtime status/warm service. |
| `app.main()` | Local JSON login and `st.session_state` establish identity/log paths. | HTTP identity dependency reading and sanitizing `X-Student-Id`; Supabase remains upstream auth authority. |
| `src/quiz_generator.py`, `mock_exam_generator.py`, `study_plan_generator.py`, `grader.py` | Several functions call `load_config()` and shared retrieval internally, limiting testability and user isolation. | Explicit config/retrieval/model injection and user-aware service inputs. |

Streamlit itself is not imported by the domain modules listed in the last row;
the problem is that their hidden global/shared dependencies prevent safe reuse
from multi-user handlers.

## Subject contract resolution

The Stage 1 baseline exposed these 12 corpus keys as selectable subjects:

`spf_chemistry`, `spf_biology`, `political_education`, `philosophy`,
`pedagogics_psychology`, `mathematics`, `physics`, `history`, `german`,
`french`, `english`, and `chemistry`.

Stage 3 resolved this mismatch. `subjects_for_display()` now returns the frozen
15 top-level IDs in contract order. `spf_biology` and `spf_chemistry` remain
concrete component corpora but are excluded from the top-level list, while the
virtual `spf_biology_chemistry` parent routes to one or both components without
creating a duplicate corpus. Explicit legacy storage/material aliases preserve
existing data non-destructively.

## RAG privacy resolution for future API handlers

`app.render_chat()` still preserves the legacy Streamlit shared-source behavior
during migration and must not be exposed as an API path. Stage 4 added
`StudentContext`, the single identity resolver, and
`retrieve_student_study_context()`. The API-safe service queries only
`user_<id>__subject_<corpus>` collections with a matching `user_id` filter,
merges approved canonical files and separately scoped student memory, supports
SPF component routing, and never queries another student's collection. Future
chat handlers must use this scoped service and disable Python transcript writes.

## Ownership boundaries

| Owner | Authoritative Stage 1 data |
| --- | --- |
| Supabase | Authentication and chat threads/messages/transcripts. |
| Frontend / localStorage | Real grades, grade averages, 0.5 display rounding, colours, planner CRUD/state, profile/prototype state, the static 15-card UI list, and SPF combined-grade display logic. |
| Python | AI inference, RAG, document parsing/indexing, indexed materials, learning goals, exam criteria, quizzes, mock exams, grading evaluation and exact formula value, study-plan proposals, feedback, source metadata, AI request metadata, and model health. |

Python may return chat AI results and metadata, but must not become a second
authoritative transcript store. Python-generated practice or audit metadata
must likewise not be mistaken for frontend-owned real grades or planner state.

## Baseline verification (2026-08-18)

Environment: `/home/kindalite/anaconda3/envs/alim_study_assistant`, Python
3.11.15. Tests and commands were run from `Code/`; no live model was required.

| Check | Result |
| --- | --- |
| `python -m py_compile app.py src/*.py` | Passed. |
| Focused baseline tests (12 relevant test modules) | Initial run: 20 passed, 1 failed because a dry-run test reached the developer's persistent Chroma DB and the fallback embedding object lacked the newer Chroma `embed_query` interface. |
| Untouched `python -m pytest -q` | Initial run: 69 passed, 2 failed for the same persistent-store test-isolation issue. |
| Focused isolation regression | 2 passed after the test-only fix. |
| Final `python -m pytest -q` | **71 passed**, with 3 Chroma legacy-embedding deprecation warnings. |
| `python scripts/smoke_test.py` | Passed all import/chunk/prompt/formula checks. |
| `python scripts/dry_run_pipeline.py` | Passed; in-memory retrieval and chat/quiz/grading prompt construction completed without Ollama. |

The only behavioral change in Stage 1 is **none**. Two tests were made
deterministic: the mock-exam dry run stubs retrieval, and the layered-retrieval
test explicitly supplies `InMemoryVectorStore`. This prevents unit tests from
reading the checkout's persistent Chroma data.

The remaining Chroma warnings indicate a future dependency-compatibility risk:
`HashEmbeddingFunction` uses a legacy embedding interface. They do not fail the
current in-memory contract but should be handled in the appropriate service or
provider stage rather than hidden in this documentation-only stage.

## Highest-risk incompatibilities

1. Shared subject retrieval in the current chat workflow is unsafe as a
   multi-user API path.
2. Subject metadata is reconciled, but future HTTP validation must call the
   new top-level/component helpers rather than accepting arbitrary corpus keys.
3. Local JSON authentication and Streamlit session identity do not match the
   Supabase-owned auth boundary.
4. Chat currently writes Python transcript history, conflicting with the
   Stage 1 ownership boundary if reused unchanged.
5. Generators and grading use implicit global config/shared retrieval, making
   safe request-scoped dependency injection difficult.
6. `MODEL_PROVIDER` is configurable but runtime, health, generation, and
   streaming behavior is Ollama-specific.
7. The current grade helper rounds to two decimals; the API must return the
   exact clamped formula value while the frontend owns 0.5 display rounding.
8. Upload/indexing currently writes shared subject folders and can rebuild an
   entire collection; it needs user-scoped validation and lifecycle handling.
9. Feedback and default performance storage are shared files unless explicitly
   scoped by the caller/config.

## Extraction recommendation

Start with a small framework-neutral subject/identity/context layer: resolve a
public subject plus optional SPF component, sanitize the student ID, resolve
that student's corpus paths/collection names, and return user-scoped learning
goals/material context. Then extract chat orchestration around that layer with
injected retrieval and model clients. This tackles the highest privacy and
contract risks first and gives later quiz, exam, plan, grading, upload, and
FastAPI handlers the same safe request-scoped foundation instead of duplicating
logic.
