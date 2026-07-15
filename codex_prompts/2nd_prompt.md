# Codex Prompt 6: Upgrade Alim Study Assistant with Local Gemma 3 4B Intelligence, OneNote-PDF Multimodal RAG, Internet/Syllabus Retrieval, Chat Audio/Image Input, and Adaptive Performance Memory

## Current Project Context

You are working on **Alim Study Assistant**, a locally hosted exam-preparation AI web app. The current repository already contains a working MVP under the `Code/` folder with:

- `app.py` Streamlit UI.
- Modular Python code under `src/`.
- Subject registry, local folders, learning goals, and exam criteria files.
- PDF/DOCX/MD/TXT text loading through `src/document_loaders.py`.
- Text chunking through `src/chunking.py`.
- ChromaDB wrapper plus in-memory test fallback through `src/vector_store.py`.
- Retrieval helpers through `src/retrieval.py`.
- Ollama text LLM client through `src/llm_client.py`.
- Prompt templates through `src/prompts.py`.
- Quiz, mock exam, study plan, grading, feedback, and stats modules.
- Beginner-readable pytest tests, smoke test, dry-run script, and README files.

Before changing anything, inspect the repository and run the existing checks from `Code/`:

```bash
pytest
python scripts/smoke_test.py
python scripts/dry_run_pipeline.py
```

The existing MVP has 25 passing tests. Preserve all existing passing behavior while adding the new functionality below.

## Mandatory Development Style

Follow the style of the previous Codex prompts and the current repository:

- Keep the app local-first and beginner-readable.
- Prefer small modules over large files.
- Add a top-level docstring to every new module.
- Add docstrings to every public function/class.
- Add concise comments for non-obvious operations so a 15-year-old learner can understand the code.
- Use type hints where simple and useful.
- Do not introduce React, FastAPI, Docker, cloud databases, authentication, Supabase, Firebase, PostgreSQL, or cloud LLM APIs.
- Do not silently delete or overwrite existing useful files.
- Preserve the Streamlit app architecture unless there is a very strong reason to refactor.
- Keep the app runnable after each implementation stage.
- Fail gracefully when optional tools such as OCR, local vision models, Whisper, or internet access are unavailable.

## New User Requirements to Implement

Implement these new requirements on top of the existing MVP:

1. The learning material root on the target machine is:

```text
/home/kindalite/AI-App/AI_Exam_Prep/learning_material
```

2. The learning material consists mainly of PDFs converted from OneNote pages. **All text on the PDFs must be considered study material. All images, diagrams, handwritten notes, screenshots, drawings, chemistry structures, graphs, and illustrations inside those PDFs must also be considered material.**

3. If material is missing for a subject, the app/model must fetch public syllabus information for **10th grade / 4th class at the public Swiss gymnasium system in Lucerne, especially Kantonsschule Alpenquai Luzern**, and use that syllabus to prepare the user for the year.

4. The app must be able to use internet access for information, question preparation, and answer analysis.

5. The chatbot must accept audio and image input to help the user understand concepts, prepare questions, and solve study queries.

6. The RAG system must use not only learning material and fetched syllabus, but also stored past performance. Past performance should adjust quiz/mock-exam difficulty and produce study-improvement suggestions.

7. The resulting app must remain local-first. Private learning material, audio, and images must not be uploaded to cloud services. Internet access is for public web retrieval only.

8. The app must be able to process and communicate in High German, English, and French. It should let the user choose the response language and should handle learning material, questions, answers, quizzes, mock exams, study plans, grading feedback, audio transcriptions, OCR text, and image descriptions in these languages where possible.

9. The app must download and use `gemma3:4b` locally through Ollama as the default intelligence layer for the system. This must replace any placeholder DeepSeek default in configuration, documentation, tests, and setup instructions. The model must be treated as a local Ollama model, not as a cloud API.

10. Before Codex confirms that the task is complete, Codex must write, save, and run a complete end-to-end testing set: unit tests, feature tests, system/smoke tests, and dry-run pipeline tests. The final completion message must include the exact commands run and their PASS/FAIL results. Codex must not claim the upgrade is done if tests were skipped, if `gemma3:4b` was not pulled/verified, or if the app cannot start.

## Official Public Source Seed URLs for Lucerne/KSA Syllabus Retrieval

Use these as seed sources for the syllabus fetcher. The code should cache retrieved documents locally and should not rely on hardcoded snippets only.

```text
https://ksalpenquai.lu.ch/profil/langzeitgymnasium
https://ksalpenquai.lu.ch/dokumente/reglemente_co/mar_faecher
https://ksalpenquai.lu.ch/profil/schwerpunktfaecher
https://ksalpenquai.lu.ch/dokumente/Lehrplaene_Untergymnasium
https://ksalpenquai.lu.ch/-/media/KSAlpenquai/Dokumente/dokumente/lehrplaene/MAR/BEI_BKD_DGym_Kantonsschule_Alpenquai_Lehrplne_MAR_2021.pdf?rev=c0bb982a13404ab9854dce61f4637f69
```

Important grade/class assumption for the app:

```text
Swiss 10th grade for this user means 4th class of the 6-year Langzeitgymnasium / MAR classes at Kantonsschule Alpenquai Luzern.
```

Do not hardcode syllabus content as final truth. Instead, implement fetch/cache/extract/index behavior so the syllabus can be refreshed when official pages change.

## Required High-Level Architecture

Add a richer RAG pipeline with four source layers:

```text
1. User learning material from /home/kindalite/AI-App/AI_Exam_Prep/learning_material
2. Local subject files already under Code/data/subjects/<subject>/
3. Cached official/public syllabus and web sources
4. Local past-performance memory
```

The answer-generation flow should become:

```text
user subject + text/audio/image query
→ convert audio to text when present
→ extract/caption/OCR image input when present
→ retrieve relevant user material chunks
→ retrieve relevant syllabus chunks when material is missing or weak
→ optionally retrieve public web chunks when internet mode is enabled
→ retrieve performance summary for this subject/topic
→ build prompt with source-priority rules
→ call local Ollama `gemma3:4b` intelligence layer
→ show answer, source list, and study suggestions
→ optionally store the interaction/performance record
```

## Source Priority Rules

Prompts and retrieval should prefer sources in this order:

1. Teacher-provided/user-provided learning material and exam criteria.
2. User learning goals.
3. Official KSA/Lucerne syllabus sources.
4. Other public web sources.
5. General model knowledge only when explicitly needed and clearly labeled as general background.

The model must say clearly when user material is missing or insufficient.

## Configuration Changes

Update `src/config.py`, `.env.example`, `requirements.txt`, and `environment.yml`.

Add settings like these:

```env
# Existing settings remain
MODEL_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
CHROMA_DB_DIR=vector_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=900
CHUNK_OVERLAP=150

# New local material root
LEARNING_MATERIAL_ROOT=/home/kindalite/AI-App/AI_Exam_Prep/learning_material

# New multimodal settings
ENABLE_PDF_PAGE_RENDERING=true
PDF_RENDER_DPI=200
ENABLE_OCR=true
OCR_LANGUAGES=deu+eng+fra
ENABLE_IMAGE_UNDERSTANDING=true
OLLAMA_VISION_MODEL=gemma3:4b

# New audio settings
ENABLE_AUDIO_INPUT=true
AUDIO_TRANSCRIPTION_BACKEND=whisper_local
WHISPER_MODEL_SIZE=base

# New internet/syllabus settings
ALLOW_INTERNET=true
ALLOW_WEB_FOR_PRIVATE_QUERIES=false
WEB_CACHE_DIR=data/web_cache
SYLLABUS_CACHE_DIR=data/web_cache/syllabus
WEB_SEARCH_PROVIDER=duckduckgo
SEARXNG_URL=
MAX_WEB_RESULTS=5
WEB_REQUEST_TIMEOUT_SECONDS=20

# New performance/adaptive learning settings
PERFORMANCE_LOG_FILE=data/performance/attempts.jsonl
PERFORMANCE_SUMMARY_FILE=data/performance/topic_mastery.json
ADAPTIVE_DEFAULT_DIFFICULTY=true

# New required local intelligence model settings
OLLAMA_REQUIRED_MODEL=gemma3:4b
AUTO_PULL_OLLAMA_MODEL=true
ALLOW_MODEL_DOWNLOAD=true
MODEL_DOWNLOAD_TIMEOUT_SECONDS=1800
```

Add optional dependencies carefully. Prefer graceful fallback if a dependency is missing.

Suggested new Python packages:

```text
pymupdf
pillow
pytesseract
beautifulsoup4
trafilatura
ddgs
streamlit-mic-recorder
faster-whisper
soundfile
```

Also document optional Linux system packages for OCR/audio:

```bash
sudo apt install tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng tesseract-ocr-fra ffmpeg
```

If these tools are missing, the app must still start and must show a clear setup message instead of crashing.


## Required Local Gemma 3 4B / Ollama Intelligence Layer

The app must use `gemma3:4b` through local Ollama as the default intelligence layer.

Implementation requirements:

1. Update `.env.example` so the default model is:

```env
MODEL_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
OLLAMA_REQUIRED_MODEL=gemma3:4b
OLLAMA_VISION_MODEL=gemma3:4b
AUTO_PULL_OLLAMA_MODEL=true
ALLOW_MODEL_DOWNLOAD=true
```

2. Update `requirements.txt` and `environment.yml` only as needed. The Python package `ollama` may be used, but the actual model must be downloaded by the Ollama runtime, not by `pip`.

3. Add setup/runtime support for the model:

```text
scripts/ensure_ollama_model.py
src/ollama_model_manager.py
```

4. `scripts/ensure_ollama_model.py` must:

- check whether the `ollama` CLI exists;
- check whether the Ollama server is reachable;
- run or request `ollama pull gemma3:4b` when the model is missing and model download is allowed;
- verify the model appears in `ollama list` or via the Ollama API after pulling;
- print beginner-readable PASS/FAIL messages;
- exit with non-zero status when the model is required but unavailable.

5. `src/ollama_model_manager.py` must implement small functions such as:

```python
def is_ollama_cli_available() -> bool: ...
def is_ollama_server_reachable(host: str) -> bool: ...
def list_ollama_models(host: str) -> list[str]: ...
def is_model_available(model_name: str, host: str) -> bool: ...
def pull_model(model_name: str, timeout_seconds: int) -> tuple[bool, str]: ...
def ensure_required_model(config: AppConfig) -> tuple[bool, str]: ...
```

6. `src/llm_client.py` must default to `gemma3:4b`, must fail gracefully when the model is missing, and must display an actionable message such as:

```text
The required local model gemma3:4b is not available. Run: ollama pull gemma3:4b
```

7. Because `gemma3:4b` supports text and image input in Ollama, use it as the default local model for both normal study reasoning and image/page understanding when `OLLAMA_VISION_MODEL` is not separately configured.

8. Do not use any paid/cloud model as the default intelligence layer. Do not silently fall back to cloud providers.

9. README files must show the exact beginner commands:

```bash
ollama --version
ollama pull gemma3:4b
ollama run gemma3:4b
ollama list
python scripts/ensure_ollama_model.py
```

10. If the user's hardware is too weak, the app may show a warning and allow configuration of another local model, but the requested default must remain `gemma3:4b`.

## New/Changed Modules

Create or update these modules. Keep functions small and readable.

### 0. `src/ollama_model_manager.py`

Purpose: make sure the required local Ollama model exists before the app depends on it.

Implement:

- `is_ollama_cli_available() -> bool`
- `is_ollama_server_reachable(host: str) -> bool`
- `list_ollama_models(host: str) -> list[str]`
- `is_model_available(model_name: str, host: str) -> bool`
- `pull_model(model_name: str, timeout_seconds: int = 1800) -> tuple[bool, str]`
- `ensure_required_model(config) -> tuple[bool, str]`

Rules:

- Use subprocess for the CLI path or Ollama API calls where simpler.
- Do not crash if Ollama is not installed.
- Do not download a model unless `AUTO_PULL_OLLAMA_MODEL=true` and `ALLOW_MODEL_DOWNLOAD=true`.
- The required default model is `gemma3:4b`.
- Return clear messages that can be shown in Streamlit and README troubleshooting.

### 1. `src/material_manifest.py`

Purpose: track every ingested learning-material file and avoid duplicate indexing.

Implement:

- `MaterialRecord` dataclass with:
  - `file_id`
  - `subject_key`
  - `source_path`
  - `source_name`
  - `source_type`
  - `sha256`
  - `modified_time`
  - `page_count`
  - `has_text`
  - `has_ocr`
  - `has_images`
  - `indexed_at`
  - `status`
  - `notes`
- `calculate_file_hash(path: Path) -> str`
- `load_manifest(path: Path) -> list[dict]`
- `save_manifest_record(record: MaterialRecord, manifest_path: Path) -> None`
- `should_reindex(path: Path, existing_record: dict | None) -> bool`

Store the manifest at:

```text
data/material_manifest.jsonl
```

### 2. `src/material_router.py`

Purpose: find files under `LEARNING_MATERIAL_ROOT` and map them to subjects.

Implement:

- `discover_learning_material(config) -> list[Path]`
- `guess_subject_from_path(path: Path, subjects: dict[str, Subject]) -> str | None`
- `group_material_by_subject(paths: list[Path], subjects: dict[str, Subject]) -> dict[str, list[Path]]`

Subject guessing should use folder names and filename keywords. Examples:

```text
bio, biology, biologie -> spf_biology or biology if added later
chem, chemistry, chemie -> chemistry or spf_chemistry
franz, französisch, french -> french
deutsch, german -> german
english, englisch -> english
history, geschichte -> history
math, maths, mathematik, physics, physik -> maths_physics
philosophy, philosophie -> philosophy
pedagogics, psychology, pädagogik, psychologie -> pedagogics_psychology
politics, politische bildung -> political_education
```

If the app cannot guess a subject, place the file in an `unassigned` list and show it in the UI for manual assignment.

### 3. `src/multimodal_pdf.py`

Purpose: properly handle OneNote-converted PDFs.

The existing `pypdf` loader only extracts text. It is not enough because OneNote PDFs can contain handwritten notes, diagrams, screenshots, and page images. Implement PDF page rendering and image-aware extraction.

Use PyMuPDF (`fitz`) where available.

Implement:

- `render_pdf_page_to_image(pdf_path: Path, page_index: int, output_dir: Path, dpi: int) -> Path`
- `extract_embedded_images(pdf_path: Path, output_dir: Path) -> list[Path]`
- `load_pdf_multimodal(pdf_path: Path, subject_key: str, config) -> list[LoadedDocument]`

For every PDF page, produce at least these document types when possible:

1. Extracted selectable PDF text.
2. OCR text from rendered page image.
3. Local vision-model description of the rendered page image.
4. Optional descriptions of embedded images.

Metadata must include:

```text
subject
source_path
source_name
source_type=pdf
page_number
modality=pdf_text | ocr_text | page_image_description | embedded_image_description
image_path when relevant
image_index when relevant
loaded_at
```

The page-level image description is required when `ENABLE_IMAGE_UNDERSTANDING=true` and `OLLAMA_VISION_MODEL` is configured. If the local vision model is unavailable, store a clear placeholder note in metadata and continue.

### 4. `src/ocr.py`

Purpose: local OCR fallback for page images and user-uploaded images.

Implement:

- `is_tesseract_available() -> bool`
- `ocr_image(image_path: Path, languages: str) -> str`
- `ocr_image_safe(image_path: Path, languages: str) -> tuple[str, str | None]`

Never crash the app if Tesseract is missing.

### 5. `src/image_understanding.py`

Purpose: create local text descriptions for images/diagrams so they can be embedded in text RAG.

Implement:

- `describe_image_with_ollama(image_path: Path, prompt: str, config) -> LLMResponse`
- `build_study_image_description_prompt(subject_key: str) -> str`
- `describe_image_safe(image_path: Path, subject_key: str, config) -> tuple[str, str | None]`

Use Ollama's local multimodal endpoint or the installed `ollama` package if suitable. Default to `gemma3:4b` for image/page understanding when no separate `OLLAMA_VISION_MODEL` is configured. The prompt should ask for:

- visible text in the image;
- diagrams and labels;
- graphs/tables;
- chemistry structures or molecule drawings;
- mathematical formulas;
- important visual relationships;
- uncertainty notes.

Do not invent details. If the image is unreadable, say so.

### 6. `src/audio_transcription.py`

Purpose: convert chatbot audio input to text locally.

Implement:

- `transcribe_audio_safe(audio_path: Path, config) -> tuple[str, str | None]`
- `is_audio_backend_available(config) -> bool`

Use a local Whisper backend if installed. Do not use cloud transcription. If unavailable, return a clear message asking the user to type the question or install the optional backend.

### 7. `src/web_retrieval.py`

Purpose: internet retrieval for public sources.

Implement:

- `WebSource` dataclass:
  - `title`
  - `url`
  - `text`
  - `snippet`
  - `fetched_at`
  - `source_type`
- `fetch_url(url: str, config) -> WebSource`
- `search_web(query: str, config, max_results: int) -> list[WebSource]`
- `cache_web_source(source: WebSource, config) -> Path`
- `load_cached_web_sources(config) -> list[WebSource]`

Support at least:

- Direct URL fetch through `requests`.
- HTML extraction through BeautifulSoup or trafilatura.
- PDF extraction through the same PDF loader pipeline where possible.
- Optional search through `ddgs` or SearXNG when configured.

Privacy rule:

- Never send full private notes, images, PDFs, or answers to a web search provider.
- If `ALLOW_WEB_FOR_PRIVATE_QUERIES=false`, only search public-safe topic queries like `Kantonsschule Alpenquai 4. Klasse Chemie Lehrplan`, not private answer text.

### 8. `src/syllabus_fetcher.py`

Purpose: fetch, cache, extract, and index KSA/Lucerne syllabus information.

Implement:

- `SYLLABUS_SEED_URLS`
- `subject_to_syllabus_keywords(subject: Subject) -> list[str]`
- `fetch_official_syllabus_sources(config) -> list[WebSource]`
- `extract_subject_syllabus_sections(subject: Subject, sources: list[WebSource]) -> list[LoadedDocument]`
- `ensure_subject_syllabus_cached(subject: Subject, config) -> list[LoadedDocument]`
- `should_fetch_syllabus_for_subject(subject: Subject, retrieval_result: RetrievalResult) -> bool`

Missing-material rule:

Fetch/index syllabus when:

- no user material is indexed for the subject;
- retrieval returns no chunks;
- all retrieved chunks are only starter learning-goal/criteria placeholders;
- the user asks for year preparation/syllabus/exam scope;
- the user explicitly enables internet/syllabus enrichment.

Store syllabus-derived documents under:

```text
data/web_cache/syllabus/<subject_key>/
```

Every syllabus chunk must include URL/source metadata and `source_layer=official_syllabus`.

### 9. `src/performance_tracker.py`

Purpose: store all practice attempts and performance signals locally.

Implement:

- `PracticeAttempt` dataclass with:
  - `attempt_id`
  - `timestamp`
  - `subject_key`
  - `topic`
  - `learning_goal`
  - `feature` such as chat, quiz, mock_exam, grader
  - `difficulty`
  - `question`
  - `student_answer`
  - `model_feedback`
  - `points_achieved`
  - `maximum_points`
  - `grade`
  - `self_rating`
  - `time_spent_seconds`
  - `source_chunk_ids`
  - `tags`
- `save_practice_attempt(attempt, config) -> dict`
- `read_practice_attempts(config, subject_key: str | None = None) -> list[dict]`
- `summarize_performance(subject_key: str, config) -> dict`
- `topic_mastery_scores(subject_key: str, config) -> dict[str, float]`

Use local JSONL by default. Do not require a database server.

### 10. `src/adaptive_learning.py`

Purpose: adapt quizzes/exams/study suggestions from past performance.

Implement:

- `choose_adaptive_difficulty(subject_key: str, topic: str, config) -> str`
- `suggest_focus_topics(subject_key: str, config, limit: int = 5) -> list[str]`
- `build_performance_context(subject_key: str, topic: str, config) -> str`
- `recommend_study_actions(subject_key: str, config) -> list[str]`

Suggested simple rules:

```text
mastery < 0.55 -> easy/revision questions and more explanation
0.55 <= mastery < 0.75 -> medium practice
mastery >= 0.75 -> harder exam-style questions
recent low scores override older high scores
unpracticed topics should be scheduled as review topics
```

Keep the algorithm simple and explain it in comments.

## Changes to Existing Modules

### `src/llm_client.py`

- Default `OLLAMA_MODEL` to `gemma3:4b`.
- Read `OLLAMA_REQUIRED_MODEL` from config and verify it with `ollama_model_manager` where appropriate.
- Keep one high-level function for text generation, but allow optional image paths for multimodal calls when needed:

```python
def generate_response(prompt: str, system_prompt: str | None = None, images: list[Path] | None = None) -> LLMResponse:
    """Generate a local response with Ollama gemma3:4b, optionally with local images."""
```

- Do not call cloud APIs.
- When Ollama or `gemma3:4b` is unavailable, return a readable error instead of raising an uncaught exception.
- Keep existing tests compatible.

### `src/config.py`

- Replace placeholder/DeepSeek defaults with `gemma3:4b` defaults.
- Add `OLLAMA_REQUIRED_MODEL`, `AUTO_PULL_OLLAMA_MODEL`, `ALLOW_MODEL_DOWNLOAD`, and `MODEL_DOWNLOAD_TIMEOUT_SECONDS`.
- Add helper properties that make the configured intelligence model and vision model easy to display in the UI.

### `src/document_loaders.py`

- Keep existing MD/TXT/DOCX behavior.
- Route PDFs through `load_pdf_multimodal` when multimodal PDF handling is enabled.
- Keep a safe fallback to the current pypdf loader.
- Extend `SUPPORTED_EXTENSIONS` with common image/audio input types only where appropriate for ingestion or chat, not necessarily subject-folder indexing.

### `src/retrieval.py`

Upgrade retrieval so it can combine:

- local subject material;
- external learning material root;
- official syllabus chunks;
- web chunks;
- performance context.

Add a higher-level function like:

```python
def retrieve_study_context(
    subject: Subject,
    query: str,
    config: AppConfig | None = None,
    include_syllabus: bool = True,
    include_web: bool = False,
    include_performance: bool = True,
    top_k: int = 6,
) -> StudyContext:
    """Return layered context for source-grounded studying."""
```

`StudyContext` should include:

- `local_context`
- `syllabus_context`
- `web_context`
- `performance_context`
- `sources`
- `warnings`
- `missing_material_detected`

Keep `retrieve_for_subject` working for existing tests.

### `src/vector_store.py`

Add support for metadata filtering if possible:

```python
query(collection_name, question, top_k=4, where: dict | None = None)
```

Use this to retrieve by source layer or modality when useful. Keep the in-memory fallback compatible with tests.

### `src/prompts.py`

Update prompts to include:

- source priority rules;
- image/audio-derived context;
- syllabus context;
- web context with URLs;
- performance context;
- adaptive difficulty explanation;
- explicit uncertainty rules.

Add prompt builders for multimodal chat:

```python
def build_multimodal_chat_prompt(...):
    """Build prompt using typed question, audio transcript, image OCR, image description, retrieved context, syllabus, web, and performance."""
```

The prompt must say:

```text
Use user material first. Use official syllabus only to fill gaps. Use web sources only when internet mode is enabled. Show sources. Do not pretend an image/audio transcript is complete if OCR/transcription was uncertain.
```

### `src/quiz_generator.py` and `src/mock_exam_generator.py`

Add adaptive difficulty support:

- Allow `difficulty="adaptive"`.
- If adaptive, call `choose_adaptive_difficulty`.
- Include performance context and focus topics in the prompt.
- Store quiz/mock-exam results when the user submits answers or self-grades.

### `src/grader.py`

After grading practice answers:

- Store the attempt in `performance_tracker` when the user confirms or when the grader has enough data.
- Include topic and learning-goal fields where possible.
- Keep the Swiss grade formula unchanged:

```text
grade = (points_achieved / maximum_points) * 5 + 1
```

### `src/stats.py`

Replace sample-only stats with local performance summaries where possible.

Add:

- average by subject;
- recent practice attempts;
- weak topics;
- recommended next difficulty;
- upcoming exam placeholder still allowed.

### `app.py`

Update the Streamlit UI with minimal changes:

#### Ingestion page

Show:

- configured learning material root;
- whether it exists;
- discovered files grouped by subject;
- unassigned files;
- button to index external learning material;
- button to fetch/cache official KSA/Lucerne syllabus;
- button to rebuild subject database including multimodal PDF chunks.

#### Chatbot page

Add:

- text question box;
- image uploader for PNG/JPG/JPEG/PDF screenshot;
- audio input or audio uploader;
- checkbox: `Use official syllabus if local material is missing`;
- checkbox: `Use internet/public web sources`;
- display of audio transcript;
- display of image OCR/description;
- answer;
- sources grouped by `local material`, `official syllabus`, `web`, `performance`;
- warnings when OCR/transcription/vision/web failed.

#### Quiz/mock exam pages

Add:

- difficulty options: `adaptive`, `easy`, `medium`, `hard`;
- show chosen adaptive difficulty and why;
- show focus topics from performance history.

#### Stats/performance page

Add:

- recent attempts table;
- topic mastery table;
- suggested improvements;
- next recommended quiz topics.

## Indexing Rules for OneNote PDFs

A OneNote-converted PDF page may contain:

- selectable text;
- scanned/bitmap text;
- handwriting;
- formulas;
- diagrams;
- screenshots;
- tables;
- arrows/labels;
- images from textbooks or teacher slides.

Do not treat `pypdf.extract_text()` as enough.

For each PDF page:

1. Extract selectable text.
2. Render the full page to an image.
3. Run OCR on the rendered page.
4. Generate a local vision description of the rendered page if configured.
5. Store each modality as separate `LoadedDocument` objects with metadata.
6. Chunk and index all document objects.
7. Display source references with page numbers and modality.

Example source display:

```text
Biology_OneNote.pdf, page 12, modality: page_image_description
Chemistry_Reactions.pdf, page 3, modality: ocr_text
```

## Internet and Privacy Rules

Internet access must be optional and visible in the UI.

The app may fetch public web pages, official syllabus pages, and public educational explanations. It must not upload private learning material or images/audio to any external service.

Rules:

- Private notes/PDF text must stay local.
- User-uploaded images/audio must stay local.
- Local Ollama may receive private context because it is local.
- Web search queries should be sanitized.
- If `ALLOW_WEB_FOR_PRIVATE_QUERIES=false`, do not use the user's full private answer or full private note text as a web query.
- Store cached web content with URL and fetch date.
- Show web URLs/sources in answers when web content was used.

## Tests to Add

Preserve all existing tests. Add new tests with mocks and temporary folders.

Create or update:

```text
tests/test_ollama_model_manager.py
tests/test_material_router.py
tests/test_material_manifest.py
tests/test_multimodal_pdf.py
tests/test_ocr.py
tests/test_image_understanding.py
tests/test_audio_transcription.py
tests/test_web_retrieval.py
tests/test_syllabus_fetcher.py
tests/test_performance_tracker.py
tests/test_adaptive_learning.py
tests/test_study_context_retrieval.py
```

Testing requirements:

- Do not require real private learning material.
- Do not require real internet for unit tests; mock web requests.
- Do not require Tesseract, Whisper, or local vision model for unit tests; test safe fallbacks.
- Do not require Ollama for unit tests.
- Use tiny generated PDFs/images where possible.
- Keep tests beginner-readable with comments.

Specific tests:

1. Material router finds files under a temporary `learning_material` root.
2. Subject guessing maps folder/file names to existing subject keys.
3. Manifest detects unchanged vs changed files.
4. Multimodal PDF loader returns page text plus page/image metadata when dependencies are mocked.
5. OCR missing backend returns a clear warning, not an exception.
6. Image understanding missing vision model returns a clear warning, not an exception.
7. Audio transcription missing backend returns a clear warning, not an exception.
8. Web retrieval caches mocked official syllabus pages.
9. Syllabus fetcher extracts only relevant subject sections where possible.
10. Retrieval falls back to official syllabus when local material is empty.
11. Performance tracker saves and reads practice attempts.
12. Adaptive learning chooses easy/medium/hard from mastery scores.
13. Quiz generator uses adaptive difficulty when selected.
14. Prompt includes local, syllabus, web, and performance contexts.
15. Existing smoke test and dry-run pipeline still pass.

Add a new dry run script:

```text
scripts/dry_run_multimodal_adaptive_pipeline.py
```

It should demonstrate without real Ollama/internet:

```text
sample PDF/image/audio placeholders
→ multimodal document objects
→ chunks
→ fake retrieval
→ fake syllabus fallback
→ fake performance context
→ adaptive difficulty
→ prompt construction
```


## Complete End-to-End Test, Feature Test, System Smoke, and Dry-Run Protocol

Codex must write, save, and run the following tests/scripts before saying the work is complete. These are mandatory completion gates, not optional suggestions.

### A. Unit Test Prompt for Codex to Implement

Create or update unit tests that verify small modules independently. Save them under `tests/`.

Required unit-test coverage:

```text
1. Configuration defaults use gemma3:4b.
2. ollama_model_manager detects missing Ollama CLI without crashing.
3. ollama_model_manager detects a mocked available gemma3:4b model.
4. ollama_model_manager calls the pull path when gemma3:4b is missing and downloads are allowed.
5. llm_client builds an Ollama request using gemma3:4b.
6. llm_client returns a helpful message when gemma3:4b is missing.
7. material_router finds and groups learning material files.
8. material_manifest detects unchanged and changed files.
9. multimodal_pdf creates page-level document objects with modality metadata using mocks.
10. OCR safe fallback returns warnings instead of exceptions.
11. image_understanding uses gemma3:4b as default vision model and safely handles unavailable Ollama.
12. audio_transcription safely handles missing local Whisper backend.
13. web_retrieval caches mocked public pages/PDFs without real internet.
14. syllabus_fetcher caches/extracts official syllabus docs using mocked fetches.
15. performance_tracker saves/reads JSONL attempts.
16. adaptive_learning chooses easy, medium, or hard from mastery scores.
17. prompts include local material, syllabus, web, image/audio context, performance context, source priority rules, and selected language.
18. quiz/mock-exam generation accepts adaptive difficulty.
19. grader still uses the Swiss grade formula exactly.
20. existing old tests still pass unchanged.
```

Run:

```bash
pytest
```

The test suite must not require real private notes, real internet, real Tesseract, real Whisper, or real Ollama for ordinary unit tests. Use mocks and temporary folders.

### B. Feature Test Prompt for Codex to Implement

Create a feature-level test file:

```text
tests/features/test_end_to_end_multimodal_adaptive_feature.py
```

The feature test must use temporary sample data and mocked external tools to test the real app pipeline across modules:

```text
create temporary learning_material root
→ create sample subject folders and a tiny fake/fixture PDF or mocked PDF pages
→ discover and assign material to a subject
→ extract selectable text + OCR text + image description as LoadedDocument objects
→ chunk documents
→ add chunks to a temporary vector store or in-memory fallback
→ mock empty local retrieval for a second subject
→ trigger official syllabus fallback through mocked web fetch
→ create a fake past-performance record
→ compute adaptive difficulty
→ build a multimodal chat prompt in High German, English, and French modes
→ verify the prompt uses source priority rules and includes source metadata
→ generate a quiz prompt with adaptive difficulty
→ grade a sample answer and store the attempt
→ read stats/performance summary
```

Assertions must verify:

- no private material is sent to web-search functions;
- source layers are preserved: `local_material`, `official_syllabus`, `web`, `performance`;
- source metadata includes file names, page numbers, modality, URLs where applicable;
- language selection affects prompt instructions;
- adaptive difficulty is explained;
- missing optional tools produce warnings, not crashes.

Run:

```bash
pytest tests/features/test_end_to_end_multimodal_adaptive_feature.py -v
```

### C. System Smoke Test Prompt for Codex to Implement

Create or update system-level smoke scripts:

```text
scripts/smoke_test.py
scripts/system_smoke_gemma3.py
```

`system_smoke_gemma3.py` must:

- load config;
- verify `OLLAMA_MODEL=gemma3:4b`;
- check whether Ollama CLI exists;
- check whether Ollama server is reachable;
- verify whether `gemma3:4b` is installed;
- if allowed, run `ollama pull gemma3:4b` or call `scripts/ensure_ollama_model.py`;
- make one tiny local model call only if Ollama and the model are available;
- print PASS/SKIP/FAIL clearly;
- exit non-zero if the task requires the model and it is still missing.

Run:

```bash
python scripts/smoke_test.py
python scripts/system_smoke_gemma3.py
```

### D. Dry-Run Pipeline Prompt for Codex to Implement

Create or update dry-run scripts:

```text
scripts/dry_run_pipeline.py
scripts/dry_run_multimodal_adaptive_pipeline.py
scripts/dry_run_full_system_no_external.py
```

`dry_run_full_system_no_external.py` must run with no internet, no Ollama, no Tesseract, and no Whisper by using mocks/fakes. It must demonstrate:

```text
config loads gemma3:4b defaults
→ fake learning material root discovered
→ fake OneNote PDF page extraction creates text/OCR/image-description docs
→ chunking works
→ retrieval returns layered StudyContext
→ missing local material triggers mocked official syllabus fallback
→ mocked web context is included only when internet mode is enabled
→ fake audio transcript and fake image OCR are added to the chat prompt
→ fake performance history chooses adaptive difficulty
→ quiz, mock exam, study plan, and grading prompts are created
→ practice attempt is saved/read locally in a temp folder
→ final PASS summary prints every step
```

Run:

```bash
python scripts/dry_run_pipeline.py
python scripts/dry_run_multimodal_adaptive_pipeline.py
python scripts/dry_run_full_system_no_external.py
```

### E. Streamlit/App Import and Startup Check Prompt for Codex to Implement

Add a check that verifies the app imports and can be launched enough to catch syntax/config errors:

```bash
python -m py_compile app.py src/*.py
python -c "import app; print('PASS app import')"
```

If feasible, add a headless Streamlit startup check with a timeout, but do not make tests flaky.

### F. Required Final Verification Commands

Before Codex says the task is complete, run this exact verification block from the project root, adapting only if the repository path requires `cd Code` first:

```bash
python scripts/ensure_ollama_model.py
python scripts/system_smoke_gemma3.py
pytest
pytest tests/features/test_end_to_end_multimodal_adaptive_feature.py -v
python scripts/smoke_test.py
python scripts/dry_run_pipeline.py
python scripts/dry_run_multimodal_adaptive_pipeline.py
python scripts/dry_run_full_system_no_external.py
python -m py_compile app.py src/*.py
```

If any command fails, fix the code or clearly state the exact failure. Do not claim completion with failing tests.

### G. Required Completion Report Format

When Codex finishes, the final message must include:

```text
Changed files:
- ...

Model verification:
- gemma3:4b pull/check: PASS or FAIL with reason

Test results:
- python scripts/ensure_ollama_model.py: PASS/FAIL
- python scripts/system_smoke_gemma3.py: PASS/FAIL
- pytest: PASS/FAIL, number of tests
- pytest tests/features/test_end_to_end_multimodal_adaptive_feature.py -v: PASS/FAIL
- python scripts/smoke_test.py: PASS/FAIL
- python scripts/dry_run_pipeline.py: PASS/FAIL
- python scripts/dry_run_multimodal_adaptive_pipeline.py: PASS/FAIL
- python scripts/dry_run_full_system_no_external.py: PASS/FAIL
- python -m py_compile app.py src/*.py: PASS/FAIL

How to run the app:
- conda activate alim-study-assistant
- ollama pull gemma3:4b
- streamlit run app.py

Known limitations:
- ...
```

Codex must not mark the task done until this report can be filled honestly.

## Documentation Updates

Update or create:

```text
README_RUN_APP.md
README_TESTING.md
README_APP_DESCRIPTION.md
README_MULTIMODAL_AND_WEB.md
```

Document:

- learning material root path;
- how to place OneNote PDFs;
- how to install optional OCR/audio dependencies;
- how to pull and verify `gemma3:4b`;
- how to configure `OLLAMA_MODEL=gemma3:4b` and `OLLAMA_VISION_MODEL=gemma3:4b`;
- how internet mode works;
- how syllabus caching works;
- how performance tracking/adaptive difficulty works;
- privacy rules;
- troubleshooting.

## Acceptance Criteria

The upgrade is complete when all of this is true:

- Existing tests still pass.
- New tests pass.
- `gemma3:4b` is configured as the default `OLLAMA_MODEL` and `OLLAMA_VISION_MODEL`.
- `scripts/ensure_ollama_model.py` can pull or verify `gemma3:4b` locally through Ollama.
- `scripts/system_smoke_gemma3.py` verifies local Gemma 3 4B availability or fails with an actionable message.
- `python scripts/smoke_test.py` still passes.
- `python scripts/dry_run_pipeline.py` still passes.
- `python scripts/dry_run_multimodal_adaptive_pipeline.py` passes without Ollama/internet.
- `streamlit run app.py` starts.
- The ingestion page can discover files from `/home/kindalite/AI-App/AI_Exam_Prep/learning_material`.
- The app can index OneNote-converted PDFs with selectable text, OCR text, and page-image descriptions when local tools are available.
- The chatbot accepts typed questions, uploaded images, and audio input/upload.
- The chatbot shows transcript/OCR/image-description warnings instead of crashing when optional tools are unavailable.
- Syllabus fetching can cache official KSA/Lucerne sources and use them when local subject material is missing.
- Internet mode can retrieve and cache public web sources, with URLs shown in answers.
- Private learning material is not sent to web search or cloud APIs.
- Quiz and mock exam difficulty can be adaptive based on local past performance.
- Performance attempts are stored locally and used to suggest study improvements.
- Source references include file names, pages, modalities, URLs, and source layers where applicable.

## Recommended Implementation Order

Work in this order so the app remains runnable:

1. Run existing tests and inspect current modules.
2. Add configuration fields and docs placeholders, replacing model placeholders with `gemma3:4b`.
2a. Add `src/ollama_model_manager.py` and `scripts/ensure_ollama_model.py`, then verify/pull `gemma3:4b`.
3. Add material manifest and material router.
4. Add safe OCR/image/audio helper modules with graceful fallbacks.
5. Add multimodal PDF loader and tests.
6. Add web retrieval and syllabus fetcher with mocked tests.
7. Upgrade retrieval to return layered `StudyContext` while keeping old functions compatible.
8. Add performance tracker and adaptive learning modules.
9. Update prompts and quiz/mock-exam/grader modules.
10. Update Streamlit UI minimally.
11. Add new unit tests, feature tests, system smoke tests, and dry-run scripts.
12. Update README files.
13. Re-run all required verification commands, including Gemma 3 4B model verification, unit tests, feature tests, smoke tests, and dry-run scripts.

## Final Instruction to Codex

Implement the upgrade carefully and incrementally. Do not replace the working MVP with a new architecture. Extend the current codebase. Preserve all existing features, tests, and documentation, then add the local `gemma3:4b` Ollama intelligence layer, multimodal PDF ingestion, official syllabus/web retrieval, chatbot audio/image input, and adaptive performance-based learning behavior described above.

Do not confirm that the task is done until:

- `gemma3:4b` is configured, pulled or verified locally through Ollama;
- all old tests pass;
- all new unit tests pass;
- the end-to-end feature test passes;
- smoke tests pass;
- dry-run system tests pass;
- the final completion report lists every required command and result.
