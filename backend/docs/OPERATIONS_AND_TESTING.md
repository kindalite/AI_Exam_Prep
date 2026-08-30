# Operations and Testing

## 1. Configuration model

`load_config()` loads `Code/.env` when python-dotenv is installed, then applies
environment variables over code defaults. Copy `.env.example` to `.env` and
adjust local paths; do not commit machine-specific values or secrets.

### Core model and retrieval

| Variables | Purpose |
| --- | --- |
| `MODEL_PROVIDER`, `OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_REQUIRED_MODEL`, `OLLAMA_VISION_MODEL` | Local Ollama identity/runtime |
| `REMOTE_LLM_BASE_URL`, `REMOTE_LLM_API_KEY`, `REMOTE_LLM_MODEL`, `REMOTE_LLM_TIMEOUT_SECONDS` | Backend-only OpenAI-compatible/vLLM configuration |
| `CHROMA_DB_DIR`, `EMBEDDING_MODEL` | Persistent vector DB and embedding model |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | Ingestion chunking |
| `AUTO_PULL_OLLAMA_MODEL`, `ALLOW_MODEL_DOWNLOAD`, `MODEL_DOWNLOAD_TIMEOUT_SECONDS` | Model preparation policy |

`MODEL_PROVIDER=ollama|openai_compatible|vllm` selects generation independently
of `EMBEDDING_MODEL`. Status/errors never expose provider secrets.

### User data

| Variables | Purpose |
| --- | --- |
| `USER_DATA_ROOT`, `AUTH_DB_FILE` | User folders and local accounts |
| `SHARED_TEMPLATE_ROOT`, `DEFAULT_TEMPLATE_USER_ID` | Safe seed material for new users |
| `ENABLE_USER_ACCOUNTS` | Account feature switch |
| `PERFORMANCE_LOG_FILE`, `PERFORMANCE_SUMMARY_FILE` | Attempt/mastery storage |

### Multimodal and web

| Variables | Purpose |
| --- | --- |
| `LEARNING_MATERIAL_ROOT` | External subject-organized course files |
| `ENABLE_PDF_PAGE_RENDERING`, `PDF_RENDER_DPI` | Page rasterization |
| `ENABLE_OCR`, `OCR_LANGUAGES` | Tesseract behavior |
| `ENABLE_IMAGE_UNDERSTANDING` | Ollama vision descriptions |
| `ENABLE_AUDIO_INPUT`, `AUDIO_TRANSCRIPTION_BACKEND`, `WHISPER_MODEL_SIZE` | Local transcription |
| `ALLOW_INTERNET`, `ALLOW_WEB_FOR_PRIVATE_QUERIES` | Network/privacy policy |
| `WEB_SEARCH_PROVIDER`, `SEARXNG_URL`, `MAX_WEB_RESULTS`, `WEB_REQUEST_TIMEOUT_SECONDS` | Public search |
| `WEB_CACHE_DIR`, `SYLLABUS_CACHE_DIR` | Local caches |

### Context and practice

| Variables | Purpose |
| --- | --- |
| `GEMMA_MAX_CONTEXT_TOKENS`, `MAX_PROMPT_INPUT_TOKENS` | Hard/model prompt limits |
| `RESERVED_OUTPUT_TOKENS`, `TOKEN_SAFETY_MARGIN` | Output and uncertainty allowance |
| `MAX_RETRIEVED_CHUNKS_PER_LAYER`, `MAX_CHARS_PER_CHUNK_IN_PROMPT` | Evidence caps |
| `ENABLE_CONTEXT_COMPRESSION` | Context trimming policy |
| `DEFAULT_QUIZ_TIMER_MINUTES`, `DEFAULT_EXAM_TIMER_MINUTES` | Timers |
| `ALLOW_AUTO_SUBMIT_ON_TIMER_END`, `HIDE_SOLUTIONS_UNTIL_GRADED` | Attempt policy |

## 2. Setup and run

From the repository root:

```bash
conda env update -p ~/anaconda3/envs/alim_study_assistant -f environment.yml --prune
conda activate ~/anaconda3/envs/alim_study_assistant
cd Code
cp .env.example .env
python scripts/verify_environment.py
python scripts/ensure_ollama_model.py
streamlit run app.py
```

Run the API independently on loopback:

```bash
uvicorn src.api.main:app --host 127.0.0.1 --port 8001
```

The example `LEARNING_MATERIAL_ROOT` contains a machine-specific absolute path.
Set it to this checkout's `AI_Exam_Prep/learning_material` directory before
ingestion. The README's historical `/home/kindalite/...` paths likewise need
adjustment on another machine.

Optional system dependencies on Debian/Ubuntu:

```bash
sudo apt install tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng tesseract-ocr-fra ffmpeg
```

Ollama must be reachable at `OLLAMA_HOST`; the configured model must be pulled.
Sentence-transformer model initialization may require a prior download/network
access unless already cached.

## 3. Verification ladder

Use the least expensive relevant checks first:

```bash
python -m py_compile app.py src/*.py
python scripts/verify_environment.py
pytest -q tests/api
pytest -q
python scripts/api_smoke_test.py
python scripts/smoke_test.py
python scripts/dry_run_full_system_no_external.py
python scripts/dry_run_lovable_contract.py
python scripts/system_smoke_user_accounts.py
python scripts/system_smoke_gemma3.py
```

The final Gemma smoke check intentionally fails when Ollama or `gemma3:4b` is
unavailable. Unit and feature tests should not require live external tools.

## 4. Test organization

| Group | Coverage |
| --- | --- |
| `tests/test_auth.py`, `test_user_*`, `test_chat_history_store.py` | Accounts and isolation |
| `test_document_loaders.py`, `test_multimodal_pdf.py`, `test_ocr.py`, `test_audio_transcription.py`, `test_image_understanding.py` | Ingestion/multimodal degradation |
| `test_chunking.py`, `test_vector_store.py`, `test_retrieval.py`, `test_rag_memory_indexer.py` | RAG pipeline and filters |
| `test_prompts.py`, `test_token_budget.py`, `test_llm_client.py` | Prompt/model boundary |
| `test_quiz_*`, `test_mock_exam_generator.py`, `test_timed_*`, `test_grader.py` | Practice lifecycle |
| `test_adaptive_*`, `test_performance_tracker.py`, `test_study_plan_generator.py` | Adaptation and planning |
| `test_phase8_stability_grounding.py` | Stability, privacy, source-grounding invariants |
| `tests/features/*` | Multi-module student workflows |

Tests rely on `tests/conftest.py` fixtures and temporary project roots. Prefer
dependency injection (`call_llm`, in-memory vector store, temporary config) over
patching global state when adding coverage.

## 5. Dry runs versus tests

- Unit tests assert narrow behavior and edge cases.
- Feature tests exercise multiple modules in-process with fakes.
- Dry-run scripts produce human-readable workflow evidence without external services.
- Smoke scripts validate environment/application integration.
- The Gemma system smoke validates the real model path.

Dry runs are useful diagnostics but do not replace assertions in pytest.

## 6. Common failure modes

| Symptom | Likely cause | Check/fix |
| --- | --- | --- |
| Streamlit import error | Wrong/incomplete environment | Install locked requirements; run verifier |
| Model unavailable | Ollama stopped or model missing | `ollama list`; run model ensure script |
| Empty retrieval | Collection not built or wrong subject collection | Use Notes Ingestion → rebuild; inspect `CHROMA_DB_DIR` |
| In-memory behavior after restart | Chroma initialization failed | Review dependency error and vector DB permissions |
| OCR empty/warning | Tesseract/language pack missing | Install executable and `deu/eng/fra` data |
| Audio warning | faster-whisper/ffmpeg/model unavailable | Run environment verifier |
| Web results empty | internet disabled, provider error, or trust filter | Review web flags/provider/cache |
| Wrong learning-material path | `.env.example` absolute path belongs to another machine | Set `LEARNING_MATERIAL_ROOT` locally |
| Timer appears reset/stale | Session artifact missing or wrong user/attempt ID | Inspect per-user `attempts/` JSON |
| Cross-user retrieval concern | Shared `retrieve_study_context` used from current chat | Switch orchestration to user-scoped retrieval |
| Torchvision runtime mismatch | torch/torchvision versions incompatible | Run dependency health/environment checks |

## 7. Adding a subject

1. Add a unique entry to `SUBJECT_DEFINITIONS` in `subject_registry.py`.
2. Add/verify its response language in `subject_languages.py`.
3. Add recognizable path aliases if material routing needs them.
4. Run `setup_subject_folders()` or launch the app to create starter files.
5. Add material and rebuild the collection.
6. Add registry, language, routing, and retrieval tests.
7. Reconcile the ID/display name with the separate frontend subject model.

## 8. Adding a material type

Update supported-extension discovery, implement a safe loader returning
`LoadedDocument`, preserve provenance metadata, route it through
`load_document()`, and test missing-dependency/malformed-input behavior. Never
execute embedded document content. Decide whether binary-derived artifacts
should be retained and where.

## 9. Adding or changing a model provider

Provider selection is implemented through `model_providers.py`. New adapters
must preserve `LLMResponse`, fake injection, safe status, stream cleanup, vision
capability reporting, token budgets, selected-provider verification, and opt-in
real-system smoke coverage.

## 10. Extending the implemented API backend

The Stage-1 API exists at `src.api.main:app`. For later endpoints:

1. Add framework-neutral orchestration before a route.
2. Freeze strict Pydantic wire models and update the generated OpenAPI document.
3. Preserve user scoping, ownership boundaries, standard errors, and timeouts.
4. Add focused API tests, the all-endpoint dry run, and full regression coverage.

## 11. Pre-change checklist

- Identify whether the path is shared, per-user, or external.
- Preserve source metadata and privacy policy through RAG changes.
- Check behavior with optional dependencies absent.
- Check Streamlit rerun/idempotency behavior.
- Ensure hidden solutions remain hidden before grading.
- Exercise prompt limits with oversized inputs.
- Run focused tests, then `pytest -q` and the appropriate dry/smoke script.
- Update this pack when a module boundary, persisted format, subject ID, or
  external contract changes.
