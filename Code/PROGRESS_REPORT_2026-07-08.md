# Progress Report - 8 July 2026

## Project

Alim Study Assistant: a local-first Streamlit exam-preparation web app using subject folders, retrieval, local Ollama prompts, quizzes, mock exams, study plans, practice grading, feedback, and tests.

## Version 0.1 - Project Skeleton Achieved

- Created the `Code/` application folder.
- Added modular Python structure under `src/`.
- Added `app.py` Streamlit entry point.
- Added `requirements.txt`, `environment.yml`, `.env.example`, and `.gitignore`.
- Added local folders for subject data, feedback, stats, and vector DB storage.

## Version 0.2 - Subject and File Logic Achieved

- Added subject registry for:
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
- Added subject-specific language defaults, paths, collection names, and instructions.
- Added safe folder setup for learning goals and exam criteria files.

## Version 0.3 - Document and Retrieval MVP Achieved

- Added loaders for MD, TXT, PDF, and DOCX files.
- Added metadata for subject, source path, source name, source type, page number where available, and load time.
- Added simple overlapping text chunking.
- Added Chroma vector store wrapper.
- Added deterministic in-memory vector store for tests and dry runs.
- Added retrieval result formatting for source-grounded prompts.

## Version 0.4 - Local LLM and Prompt MVP Achieved

- Added Ollama client using `OLLAMA_HOST` and `OLLAMA_MODEL`.
- Added graceful error handling when Ollama is unavailable.
- Added prompt templates for:
  - subject chatbot
  - quiz generation
  - mock exam generation
  - study plan generation
  - practice grading
  - feedback analysis
- Prompts instruct the model to use provided sources and state when material is insufficient.

## Version 0.5 - Study Features Achieved

- Added subject chatbot flow.
- Added learning goal connector.
- Added quiz generator.
- Added mock exam generator.
- Added study plan generator.
- Added practice grader using:

```text
grade = points_achieved / maximum_points * 5 + 1
```

- Added feedback saving to local JSONL.
- Added basic stats and planner placeholders.

## Version 0.6 - Documentation Achieved

- Added `README_RUN_APP.md` for installation and starting the app.
- Added `README_TESTING.md` for unit tests, smoke tests, and dry runs.
- Added `README_APP_DESCRIPTION.md` explaining the project, features, privacy, and educational purpose.
- Added starter `README.md` for navigation.

## Version 0.7 - Testing Achieved

- Added pytest setup and sample test data.
- Added tests for:
  - environment sanity
  - subject registry
  - document loaders
  - chunking
  - vector store
  - retrieval
  - LLM client payload/error handling
  - prompts
  - quiz generator
  - mock exam generator
  - study plan generator
  - grader
  - feedback
  - app import smoke check
- Added `scripts/smoke_test.py`.
- Added `scripts/dry_run_pipeline.py`.

## Verification on 8 July 2026

Executed from `Code/`:

```bash
pytest
python scripts/smoke_test.py
python scripts/dry_run_pipeline.py
```

Results:

- `pytest`: 25 passed.
- Smoke test: passed.
- Dry-run pipeline: passed.
- Streamlit server: started at `http://localhost:8501`.

Note: tests were run in the current shell with Python 3.13. The documented target environment remains the Conda environment `alim-study-assistant` with Python 3.11.

## Still Needed for Version 1.0 Testable Beta

- Install and verify the full Conda environment with the exact package versions.
- Manually check each Streamlit UI page in the browser.
- Confirm Chroma persistence with real local files and multiple subject collections.
- Pull and configure the actual local DeepSeek Distilled Ollama model.
- Test chatbot, quiz, exam, plan, and grader features against the real Ollama model.
- Add private school material to subject folders and build each subject database.
- Add stronger PDF and DOCX fixture coverage.
- Add optional Ollama integration tests marked separately from unit tests.
- Improve the Streamlit UI after real user testing.
- Add persistent local grade table editing instead of sample rows only.
- Add better planner storage for upcoming exams and to-do tasks.
- Add image/diagram handling for chemistry only after the text workflow is stable.
- Add more subject-specific prompt refinements after feedback from real study sessions.
- Review privacy defaults before any GitHub push to ensure private notes, `.env`, and `vector_db/` are excluded.

## Current Status

The project is a working local-first MVP codebase at version `0.7`. It is ready for environment installation, Streamlit manual testing, real subject material indexing, and Ollama model validation on the path toward version `1.0` testable beta.
