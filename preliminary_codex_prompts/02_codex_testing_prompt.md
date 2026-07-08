# Common Project Context for Codex

You are working on **Alim Study Assistant**, a locally hosted exam-preparation AI web app for a student. This is an educational project for a 15-year-old learner, so the code must be simple, modular, traceable, and understandable.

## Mandatory Development Style

- Keep the folder/code structure modular to ensure traceability and manageability.
- Prefer small, clear Python modules over large monolithic files.
- Add docstrings for every public function, class, and module.
- Add concise inline comments for important lines and every non-obvious operation so a 15-year-old learner can follow the code.
- Use descriptive variable names.
- Avoid clever abstractions unless they clearly improve readability.
- Do not introduce React, FastAPI, Docker, cloud services, authentication, or complex databases unless explicitly requested later.
- Do not silently delete or overwrite existing files. Inspect the repository first and preserve useful existing work.
- Implement features incrementally and make the app runnable after each stage.
- Prefer local-first behavior and safe fallbacks when files, folders, or models are missing.

## Stack to Use

Use the already discussed Python/Conda stack:

- Python 3.11 in a conda environment named `alim-study-assistant`.
- Streamlit for the locally hosted web app UI.
- Local files for subject material, notes, syllabus, learning goals, and exam criteria.
- ChromaDB for local vector stores, with separate collections/databases per subject.
- Sentence Transformers for local embeddings.
- Ollama Python client or local HTTP calls for the locally hosted LLM.
- Local DeepSeek Distilled model served through Ollama, configured so VRAM/RAM usage stays within the available limit, max roughly 16 GB VRAM occupancy.
- pandas for grade/stat tables and feedback logs.
- python-dotenv for local configuration.
- requests if direct HTTP calls to Ollama are simpler.
- pypdf for PDF ingestion.
- python-docx for DOCX ingestion.
- pytest for tests.

Expected package names may include:

```text
streamlit
python-dotenv
requests
pandas
chromadb
sentence-transformers
ollama
pypdf
python-docx
pytest
```

## Local LLM Requirement

- The app must run locally.
- The LLM backend must default to Ollama.
- The model name must be configurable through `.env`, for example `OLLAMA_MODEL=deepseek-distilled-local` or another available DeepSeek distilled Ollama model name.
- The Ollama host must be configurable through `.env`, for example `OLLAMA_HOST=http://localhost:11434`.
- The app must fail gracefully if Ollama is not running or if the model is missing.
- Do not require any paid API for the default app path.

## Input Material Requirement

The LLM must refer to subject syllabus, learning goals, notes, uploaded material, and examination criteria. These source materials may be in:

- `.docx`
- `.pdf`
- `.md`
- `.txt`

The app must be able to ingest and index these formats where feasible. Use clear source metadata so retrieved answers can show where information came from.

## Subject Criteria to Support

Build the app so each subject can have its own criteria file and subject-specific behavior. Include at least these subjects and criteria assumptions:

- **SPF Chemistry**: German; analyze exercises; create similar exercises; answer questions about current topic; draw/describe molecules; focus on exercises.
- **SPF Biology**: German; analyze material; answer questions; read pages/PDFs.
- **Political Education**: German; analyze material; answer questions; read pages/PDFs.
- **Philosophy**: German; analyze material; answer questions; read pages/PDFs.
- **Pedagogics/Psychology**: German; analyze material; answer questions; read pages/PDFs.
- **Maths/Physics**: English; generate similar problems; produce correct answers; show correct solution method.
- **History**: English; analyze book/OneNote material; adapt to learning goals; test all material given; place events/texts in historical context.
- **German**: German; create quizlets from unknown vocabulary asked by the user; know treated books; create class-style questions; correct texts and give writing-style tips.
- **French**: simple B1 French; create quizlets from vocabulary pages; generate similar exercises and exams; explain grammar topics.
- **English**: English; analyze grammar exercises and replicate them; analyze books and ask class-style questions.
- **Chemistry**: German; understand images/graphics/models explaining concepts; use chemistry knowledge only within class scope; draw/describe simple wedge-dash formulas and possibly 3D molecule descriptions.

## Grading Formula

Use this grading formula where point-based grading is needed:

```text
grade = (points_achieved / maximum_points) * 5 + 1
```

Clamp or validate values so invalid inputs do not produce impossible grades.

## Product Requirements to Address

- Separate chatbot behavior for each subject.
- Separate local database/vector collection for each subject.
- Connect learning goals with Alim's notes/material and retrieve exam-relevant information.
- Generate mock exams and quizzes based on learning goals, notes, material, relevant database information, and subject-specific exam criteria.
- Generate a scheduled learning plan for the subject.
- Provide an exam grader based on each subject's examination criteria.
- Support German and English language behavior.
- Improve through user feedback stored locally.
- Keep UI minimal; UI is not the critical part.
- Support a main menu, school page, subject folders, notes, quiz bot, stats, calendar/planner placeholders, and upcoming exams where reasonable.


# Codex Prompt 2: Build Tests, Smoke Tests, Dry Runs, and System Sanity Checks

## Your Task

Create a complete testing setup for the **Alim Study Assistant** app. The goal is to make sure the app's core features are sane, testable, and safe to change.

The tests must be beginner-readable. Add docstrings and comments explaining what each test checks and why it matters.

## Testing Scope

Create tests for:

- Environment sanity.
- Folder structure sanity.
- Subject registry sanity.
- Document loading.
- Chunking.
- Retrieval/vector store behavior using small sample data.
- LLM client error handling.
- Prompt construction.
- Quiz/mock exam/study plan/grader functions.
- Grading formula.
- Feedback storage.
- Basic Streamlit smoke test where feasible.

## Required Test Folder Structure

Create or adapt:

```text
tests/
  __init__.py
  conftest.py
  test_environment.py
  test_subject_registry.py
  test_document_loaders.py
  test_chunking.py
  test_vector_store.py
  test_retrieval.py
  test_llm_client.py
  test_prompts.py
  test_quiz_generator.py
  test_mock_exam_generator.py
  test_study_plan_generator.py
  test_grader.py
  test_feedback.py
  test_smoke_app_import.py

test_data/
  biology_sample.md
  chemistry_sample.md
  learning_goals_sample.md
  exam_criteria_sample.md
```

If the repo already has a different structure, adapt safely but keep tests modular and traceable.

## Unit Tests

### 1. Environment Tests

Check that:

- Python version is compatible with Python 3.11.
- Key packages can be imported:
  - streamlit
  - chromadb
  - sentence_transformers
  - pandas
  - dotenv
  - pypdf
  - docx
  - pytest

Do not require Ollama to be running for unit tests.

### 2. Subject Registry Tests

Check that:

- Each required subject exists.
- Each subject has a collection name.
- Each subject has a default language.
- Each subject has a path for notes/material.
- Each subject has criteria/learning goal fields.

Required subjects:

- SPF Chemistry
- SPF Biology
- Political Education
- Philosophy
- Pedagogics/Psychology
- Maths/Physics
- History
- German
- French
- English
- Chemistry

### 3. Document Loader Tests

Test loading:

- `.md`
- `.txt`
- `.pdf` if easy using a minimal fixture or mocked loader
- `.docx` if easy using a minimal generated fixture or mocked loader

Each loaded document must include metadata:

- source path;
- subject;
- file type;
- text content.

### 4. Chunking Tests

Test that:

- a short text returns one chunk;
- a long text returns multiple chunks;
- overlap works;
- empty text returns an empty list or safe result;
- metadata is preserved.

### 5. Vector Store and Retrieval Tests

Use tiny sample chunks. Do not require real school notes.

Test that:

- a subject collection can be created;
- chunks can be added;
- a query returns at least one relevant result;
- subjects remain separated;
- missing collection gives a helpful message.

If Chroma or embedding model makes tests slow, mark these as integration tests or use temporary test directories.

### 6. LLM Client Tests

Do not call a real model in unit tests.

Test that:

- missing Ollama host is handled;
- connection failure returns a readable error;
- prompt payload is built correctly;
- provider defaults to Ollama.

Use mocks for HTTP calls.

### 7. Prompt Tests

Check that generated prompts include:

- subject name;
- selected language;
- retrieved notes/context;
- exam criteria;
- instruction to use only provided sources;
- instruction to state when source material is insufficient.

### 8. Grader Tests

Test grading formula:

```text
grade = points_achieved / maximum_points * 5 + 1
```

Include cases:

- 0/max gives grade 1.
- max/max gives grade 6.
- half points gives grade 3.5.
- invalid max points raises error or returns safe validation message.
- points above max are rejected or clamped according to implementation.

### 9. Feedback Tests

Test that feedback:

- saves to JSONL or CSV;
- contains timestamp;
- contains subject and feature;
- preserves user rating/comment;
- can be read back.

## Smoke Tests

Create a script or pytest file that checks:

- `app.py` can be imported without crashing.
- Key modules can be imported.
- Sample subject material can be loaded.
- Sample chunks can be created.
- A prompt can be generated.
- Grading formula works.

Do not require the LLM to run for smoke tests.

Suggested file:

```text
scripts/smoke_test.py
```

The script should print clear PASS/FAIL messages and exit with non-zero status on failure.

## Dry Run Tests

Create a dry-run mode for the app or a script:

```text
scripts/dry_run_pipeline.py
```

Dry-run pipeline:

```text
sample subject
→ sample notes
→ chunk notes
→ create temporary vector store
→ retrieve chunks
→ build answer prompt
→ build quiz prompt
→ build grading prompt
→ print outputs without calling the real LLM
```

This dry run must not require Ollama.

## Test Documentation

Add brief comments in each test explaining:

- what the test is checking;
- why it matters for the app;
- what a failure usually means.

## Acceptance Criteria

Testing work is complete when:

- `pytest` runs successfully.
- `python scripts/smoke_test.py` runs successfully.
- `python scripts/dry_run_pipeline.py` runs successfully.
- Tests do not require private school data.
- Tests do not require Ollama to be running except optional integration tests.
- Tests use temporary directories where needed.
- Test code is commented and beginner-readable.
