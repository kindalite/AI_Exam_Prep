# Module Reference

This is the file-level map for executable code. “Entry points” lists the most
important callable surface, not every private helper.

## Application and UI

| File | Responsibility | Main entry points |
| --- | --- | --- |
| `app.py` | Streamlit composition root and page renderers | `main`, `render_chat`, `render_ingestion`, `render_grader`, `render_stats` |
| `src/ui_auth.py` | Login/register screen and session-state identity | `require_login` |
| `src/ui_navigation.py` | Stable sidebar labels | `page_labels` |
| `src/ui_practice_modes.py` | Focused timed quiz/exam UI | `render_quiz_mode`, `render_exam_mode` |
| `src/ui_subject_dashboard.py` | Subject overview and recommendations | `render_subject_dashboard` |
| `src/ui_docs.py` | Student-facing in-app help | `render_help_page` |
| `src/ui_components.py` | Small reusable Streamlit cards | `status_card`, `action_card` |

`app.py` is intentionally thin in some paths but still contains direct workflow
orchestration for chat, ingestion, study-plan generation, grading, feedback, and
stats. The parallel HTTP adapter uses `src/services/` and never depends on
Streamlit state.

## FastAPI and service layer

| Path | Responsibility | Main entry points |
| --- | --- | --- |
| `src/api/main.py` | FastAPI factory, CORS, middleware, route registration | `app`, `create_app` |
| `src/api/routes/` | Thin health, subject, import, chat, study-tool, feedback adapters | route functions |
| `src/api/schemas/` | Strict Lovable Pydantic request/response contracts | exported schema models |
| `src/services/` | Framework-neutral orchestration and injection seams | `run_api_chat`, `generate_*_api`, `import_student_document` |
| `src/ai_metadata_store.py` | Per-user non-authoritative AI provenance | `save_ai_provenance`, `find_ai_provenance` |

## Configuration, subjects, and utilities

| File | Responsibility | Main entry points |
| --- | --- | --- |
| `src/config.py` | Load `.env`, resolve paths, type all settings | `AppConfig`, `load_config` |
| `src/subject_registry.py` | Define the 15 top-level API subjects, SPF component corpora, and paths/languages | `Subject`, `build_subject_registry`, `subjects_for_display`, `corpus_keys_for_request`, `setup_subject_folders` |
| `src/subject_languages.py` | Required answer-language mapping | `language_for_subject`, `language_instruction` |
| `src/utils.py` | UTC timestamps, directories, guarded file/text helpers | `utc_timestamp`, `ensure_directory`, `read_text_if_exists` |

The previous 12-subject mismatch is resolved. The display/API model contains
exactly 15 stable top-level IDs in frontend order. SPF Biology and SPF
Chemistry remain concrete component corpora nested beneath the virtual
`spf_biology_chemistry` parent; explicit aliases preserve legacy storage.

## Authentication and user storage

| File | Responsibility | Main entry points |
| --- | --- | --- |
| `src/auth.py` | PBKDF2 hashing and JSON account database | `add_user_record`, `authenticate_from_db`, `load_auth_db` |
| `src/user_manager.py` | Account creation, folder setup, safe template copy | `create_user`, `authenticate_user`, `list_users` |
| `src/user_data_paths.py` | Sanitized user directories and vector names | `ensure_user_data_structure`, `get_user_subject_root`, collection-name helpers |
| `src/chat_history_store.py` | Per-user chat JSONL and uploaded media | `save_chat_message`, `read_chat_messages`, `save_chat_media`, `chat_messages_to_documents` |
| `src/practice_store.py` | Generated sets, hidden solutions, answers, reports | `save_generated_quiz`, `save_generated_exam`, `save_submitted_answers`, `save_performance_report` |
| `src/attempt_session.py` | Serializable timer state across reruns | `create_timed_session`, `load_timed_session`, `seconds_remaining`, `mark_session_status` |

## Document ingestion and vector retrieval

| File | Responsibility | Main entry points |
| --- | --- | --- |
| `src/material_router.py` | Discover supported external files and infer subject | `discover_learning_material`, `guess_subject_from_path`, `group_material_by_subject` |
| `src/material_manifest.py` | SHA-256 change tracking in a JSONL manifest | `calculate_file_hash`, `should_reindex`, `save_manifest_record` |
| `src/document_loaders.py` | MD/TXT/PDF/DOCX/SVG/image normalization | `load_document`, `load_subject_documents`, `iter_material_files` |
| `src/multimodal_pdf.py` | PDF text, rendered-page OCR, and image descriptions | `load_pdf_multimodal`, `render_pdf_page_to_image`, `extract_embedded_images` |
| `src/chunking.py` | Overlapping text chunks with preserved metadata | `chunk_text`, `chunk_documents` |
| `src/embeddings.py` | Sentence-transformer or deterministic fallback embeddings | `get_embedding_function`, `HashEmbeddingFunction` |
| `src/vector_store.py` | Common Chroma/in-memory rebuild and query behavior | `ChromaVectorStore`, `InMemoryVectorStore`, `RetrievedChunk` |
| `src/retrieval.py` | Index construction and layered retrieval | `build_subject_index`, `retrieve_study_context`, user-scoped index/retrieve helpers |
| `src/rag_memory_indexer.py` | Convert and index user history/practice memory | `build_rag_documents_from_user_history`, `index_user_memory_for_subject`, `retrieve_user_memory` |

Supported material extensions are defined by the loaders/router and include
Markdown, plain text, PDF, DOCX, PNG, JPG/JPEG, and SVG. Source metadata carries
fields such as subject, source name/path, page, modality, URL, source layer,
chunk ID, and (for user indexes) user ID.

## Model, prompts, and token control

| File | Responsibility | Main entry points |
| --- | --- | --- |
| `src/llm_client.py` | Provider-neutral legacy-compatible generation seam | `generate_response`, `build_ollama_payload`, `LLMResponse` |
| `src/model_providers.py` | Ollama and OpenAI-compatible/vLLM adapters | `build_model_provider`, provider classes |
| `src/model_runtime.py` | Provider status, warmup, and streaming compatibility | `verify_model_runtime`, `warm_model`, `stream_chat_tokens` |
| `src/ollama_model_manager.py` | CLI/API model discovery and optional pull | `list_ollama_models`, `is_model_available`, `ensure_required_model` |
| `src/prompts.py` | System/chat/quiz/exam/plan/grading prompt templates | `build_multimodal_chat_prompt` and `build_*_prompt` functions |
| `src/token_budget.py` | Priority packing and hard context enforcement | `budget_context_sections`, `assert_prompt_under_limit`, `build_token_budget_report` |

Generation helpers accept optional injected `call_llm` functions. Tests and dry
runs use this seam to validate orchestration without Ollama.

## Practice, grading, and adaptation

| File | Responsibility | Main entry points |
| --- | --- | --- |
| `src/quiz_generator.py` | General quiz prompt + model call | `create_quiz` |
| `src/mock_exam_generator.py` | General exam paper prompt + model call | `create_mock_exam` |
| `src/study_plan_generator.py` | Study-plan prompt + model call | `create_study_plan` |
| `src/grader.py` | Swiss formula and AI feedback | `calculate_grade`, `create_grading_feedback`, `store_grading_attempt` |
| `src/quiz_mode.py` | Focused quiz generation and timed start | `generate_quiz_set`, `start_quiz_mode` |
| `src/exam_mode.py` | Focused exam generation and timed start | `generate_exam_set`, `start_exam_mode` |
| `src/timed_practice.py` | Split questions/solutions and submit/grade lifecycle | `start_practice_attempt`, `submit_and_grade_attempt` |
| `src/performance_tracker.py` | Practice JSONL and mastery aggregation | `new_attempt`, `save_practice_attempt`, `summarize_performance`, `topic_mastery_scores` |
| `src/adaptive_learning.py` | Difficulty and weak-topic rules | `choose_adaptive_difficulty`, `suggest_focus_topics`, `recommend_study_actions` |
| `src/stats.py` | Grade tables, averages, targets, app summaries | `average_grade`, `desired_grade_points`, `subject_performance_summary` |

Swiss formula grading is `1 + 5 × achieved / maximum`, with input validation and
rounding implemented in `grader.calculate_grade`.

## Multimodal, web, and evidence

| File | Responsibility | Main entry points |
| --- | --- | --- |
| `src/ocr.py` | Local Tesseract OCR with safe warnings | `ocr_image_safe` |
| `src/image_understanding.py` | Ollama vision descriptions | `describe_image_safe` |
| `src/audio_transcription.py` | Local faster-whisper transcription | `transcribe_audio_safe` |
| `src/syllabus_fetcher.py` | Fetch/cache official syllabus and select subject sections | `ensure_subject_syllabus_cached`, `should_fetch_syllabus_for_subject` |
| `src/web_retrieval.py` | Search/fetch/extract/cache public pages | `search_web`, `fetch_url`, `cache_web_source` |
| `src/source_policy.py` | Query sanitization and trusted-source checks | `sanitize_public_query`, `is_trusted_source` |
| `src/source_citations.py` | Evidence labels and grouping | `source_label`, `group_sources` |
| `src/web_permission.py` | Session-scoped permission model | `WebPermission`, `permission_from_choice` |

## Feedback, diagnostics, and reliability

| File | Responsibility | Main entry points |
| --- | --- | --- |
| `src/feedback.py` | Append/read local feedback JSONL | `save_feedback`, `read_feedback` |
| `src/app_logging.py` | Redacted app/session diagnostic JSONL | `append_log`, `new_app_run_log`, `new_user_session_log` |
| `src/operation_tracker.py` | Recoverable in-memory long-operation state | `OperationTracker`, `OperationState` |
| `src/performance_monitor.py` | Timed-operation metrics JSONL | `measure_operation`, `record_metric` |
| `src/dependency_health.py` | Torch/torchvision compatibility diagnostics | `check_torchvision_compatibility` |

## Operational scripts

| Script | Purpose |
| --- | --- |
| `verify_environment.py` | Python, packages, paths, external tools, and model prerequisites |
| `ensure_ollama_model.py` | Check/pull the configured Ollama model |
| `system_smoke_gemma3.py` | Real Ollama/model system smoke test |
| `system_smoke_user_accounts.py` | Local auth and isolated folder smoke test |
| `smoke_test.py` | Fast application-basics smoke test |
| `migrate_single_user_to_user_storage.py` | Non-destructively copy legacy data into per-user layout |
| `dry_run_pipeline.py` | Core RAG flow without Ollama |
| `dry_run_multimodal_adaptive_pipeline.py` | Multimodal/adaptive flow with fakes |
| `dry_run_full_system_no_external.py` | Broad workflow without network/model/OCR/Whisper |
| `dry_run_user_isolated_rag.py` | User collection and filter isolation |
| `dry_run_timed_quiz_exam.py` | Timer, hidden solution, submission, report lifecycle |
| `dry_run_token_budget_128k.py` | Oversized synthetic context packing |
| `dry_run_full_student_system.py` | Full local student workflow with fakes |
| `api_smoke_test.py` | In-process health/catalogue/docs smoke |
| `dry_run_lovable_contract.py` | All Lovable endpoints with temporary fakes |
| `smoke_local_ollama.py`, `smoke_remote_openai_compatible.py` | Explicit opt-in provider smokes |

## Tests

`tests/test_*.py` contains focused unit/component tests. `tests/features/`
contains end-to-end-in-process feature tests for multimodal adaptive learning,
user-isolated RAG/practice, timed modes, and token packing. Most external
services are mocked; `system_smoke_gemma3.py` is the deliberate real-model check.
