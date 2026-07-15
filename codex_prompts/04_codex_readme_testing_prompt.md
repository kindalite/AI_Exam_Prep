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


# Codex Prompt 4: Create README for Running Unit Tests, Smoke Tests, and Dry Run Tests

## Your Task

Create or update a README explaining how to run all tests for **Alim Study Assistant**.

Suggested output file:

```text
README_TESTING.md
```

This README must be beginner-friendly and explain what each type of test means.

## Required Sections

### 1. Purpose of Testing

Explain in simple terms:

- Unit tests check small pieces of code.
- Smoke tests check whether the app and key modules basically start.
- Dry run tests check the app pipeline without calling the real LLM.
- Integration tests may check Chroma or Ollama but should be optional.

### 2. Activate the Environment

Include:

```bash
conda activate alim-study-assistant
```

Explain that tests must be run from the project root.

### 3. Run Unit Tests

Include:

```bash
pytest
```

Also include optional verbose version:

```bash
pytest -v
```

### 4. Run a Specific Test File

Include examples:

```bash
pytest tests/test_grader.py
pytest tests/test_chunking.py
pytest tests/test_document_loaders.py
```

### 5. Run Smoke Test

If a smoke test script exists, document:

```bash
python scripts/smoke_test.py
```

Explain expected output.

### 6. Run Dry Run Pipeline

If a dry-run pipeline script exists, document:

```bash
python scripts/dry_run_pipeline.py
```

Explain that this should not require Ollama and should not call the local LLM.

### 7. Optional Ollama Integration Test

If implemented, document how to run it separately, for example:

```bash
pytest tests/test_ollama_integration.py -m integration
```

Explain that Ollama must be running and the configured model must be available.

### 8. Test Data

Explain:

- Tests should use sample data only.
- Tests should not require private school notes.
- Test fixtures live in `test_data/` or `tests/fixtures/`.

### 9. What to Do When Tests Fail

Explain common failure causes:

- Environment not activated.
- Missing package.
- Wrong working directory.
- Missing sample files.
- Chroma temporary directory issue.
- Ollama not running for optional integration tests.

### 10. Testing Checklist Before Changing Code

Add a checklist:

```text
[ ] Conda environment is activated
[ ] App imports successfully
[ ] Unit tests pass
[ ] Smoke test passes
[ ] Dry run pipeline passes
[ ] Optional integration tests pass if Ollama is available
```

## Style Requirements

- Use simple language.
- Include copy-pasteable commands.
- Explain each command briefly.
- Keep the README modular and easy to update.
