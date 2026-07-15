# Alim Study Assistant - Codex Prompt Pack

# File: 01_codex_main_app_architecture_prompt.md

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


# Codex Prompt 1: Build the Main App Architecture and Logic

## Your Task

Build the main architecture and logic for the locally hosted **Alim Study Assistant** app using the stack and requirements above.

This prompt is for creating the main application, folder structure, core modules, RAG pipeline, subject logic, local LLM integration, quiz/mock-exam/study-plan/grader features, and basic Streamlit UI.

## Important Scope Rule

Build a useful local-first MVP. Do not over-engineer. Do not add cloud hosting, user accounts, React, FastAPI, Docker, PostgreSQL, Supabase, Firebase, or external APIs unless there is already code for them and they are explicitly required.

## Required Repository Structure

Create or adapt the repository to a modular structure similar to this:

```text
alim-study-assistant/
  app.py
  README.md
  requirements.txt
  environment.yml
  .env.example
  .gitignore

  data/
    subjects/
      biology/
        notes/
        syllabus/
        criteria/
        learning_goals.md
        exam_criteria.md
      chemistry/
        notes/
        syllabus/
        criteria/
        learning_goals.md
        exam_criteria.md
      german/
      french/
      english/
      maths_physics/
      history/
      political_education/
      philosophy/
      pedagogics_psychology/
      spf_chemistry/
      spf_biology/

  vector_db/

  src/
    __init__.py
    config.py
    subject_registry.py
    document_loaders.py
    chunking.py
    embeddings.py
    vector_store.py
    retrieval.py
    llm_client.py
    prompts.py
    quiz_generator.py
    mock_exam_generator.py
    study_plan_generator.py
    grader.py
    feedback.py
    stats.py
    utils.py

  tests/
    __init__.py
```

If existing files already exist, inspect them first and adapt rather than replacing blindly.

## Feature Requirements

### 1. Streamlit App Shell

Build a local Streamlit app with:

- Main menu/home page.
- Minimal two-colour theme if feasible.
- Subject selector.
- Language selector: German / English.
- Pages or sections for:
  - Subject chatbot.
  - Learning goals.
  - Quiz generator.
  - Mock exam generator.
  - Study plan generator.
  - Exam grader.
  - Notes/material ingestion.
  - Feedback.
  - Basic stats/planner placeholders.
- UI can be simple. Correct logic and traceability matter more than visual polish.

### 2. Subject Registry

Implement a subject registry/configuration module.

Each subject should define:

- internal subject key;
- display name;
- default language;
- notes/material folder;
- syllabus folder;
- criteria folder/file;
- learning goals file;
- Chroma collection name;
- subject-specific instructions.

### 3. Document Loading

Implement document loading for:

- Markdown files.
- Text files.
- PDF files through `pypdf`.
- DOCX files through `python-docx`.

Every loaded document chunk must retain metadata:

- subject;
- source file path;
- source file name;
- source type;
- page number if available;
- chunk ID;
- loaded timestamp if useful.

### 4. Chunking

Implement simple chunking with overlap.

Requirements:

- Configurable chunk size and overlap.
- Preserve metadata.
- Make the function easy to understand and test.
- Add comments explaining chunking because this is an educational project.

### 5. Embeddings and Vector Store

Implement local embeddings using Sentence Transformers.

Implement Chroma vector store support:

- Separate collection per subject.
- Ability to build/rebuild an index for a subject.
- Ability to retrieve top-k relevant chunks for a user question, learning goal, or exam task.
- Store Chroma data locally under `vector_db/`.
- Show clear errors when no notes are indexed.

### 6. Local LLM Client

Implement an Ollama client that:

- Reads `OLLAMA_HOST` and `OLLAMA_MODEL` from `.env` or environment variables.
- Uses either the `ollama` Python client or `requests` to call `http://localhost:11434/api/chat`.
- Has a single high-level function such as `generate_response(prompt, system_prompt=None)`.
- Handles connection errors gracefully.
- Makes it easy to later add OpenAI/Gemini providers, but default is local Ollama.

### 7. Prompt System

Create prompt templates for:

- Subject chatbot answers.
- Quiz generation.
- Mock exam generation.
- Study plan generation.
- Exam grading.
- Feedback analysis.

All prompts must instruct the model to:

- Use retrieved notes, syllabus, learning goals, and exam criteria.
- State clearly when material is not found in the provided sources.
- Show source snippets or source file names when possible.
- Respect the selected language.
- Respect subject-specific criteria.
- Avoid hallucinating exam rules not present in source files.

### 8. Subject Chatbot

Build a chatbot flow:

```text
subject + language + user question
→ retrieve subject-specific chunks from subject database
→ include syllabus/criteria/learning goals if relevant
→ call local LLM
→ show answer + sources
```

Each subject must use its own Chroma collection.

### 9. Learning Goal Connector

Implement functionality to:

- Load learning goals for each subject.
- Let the user select or paste a learning goal.
- Retrieve relevant notes/material for that learning goal.
- Summarize what is exam-relevant.
- Identify possible missing material if retrieval is weak.

### 10. Quiz Generator

Generate quizzes based on:

- selected subject;
- selected learning goal;
- retrieved notes/material;
- subject-specific exam criteria;
- selected language;
- selected difficulty.

Output should include:

- questions;
- answer key;
- short explanation;
- source references where possible.

Subject-specific examples:

- French: B1-level vocabulary/grammar exercises.
- German: vocabulary quizlets, book questions, text correction tasks.
- Maths/Physics: similar problems with correct solution method.
- Chemistry: exercise-focused questions and molecule descriptions.
- History: historical-context questions.

### 11. Mock Exam Generator

Generate exam-style practice papers based on:

- subject criteria;
- notes/material;
- learning goals;
- number of points;
- difficulty;
- selected language.

Output must include:

- exam paper;
- marking scheme;
- model answers;
- point allocation;
- sources.

### 12. Study Plan Generator

Generate a scheduled learning plan using:

- subject;
- exam date;
- available hours/week;
- weak topics;
- learning goals;
- retrieved relevant material.

Output should include:

- weekly or daily schedule depending on user input;
- revision tasks;
- quiz/mock exam checkpoints;
- priority topics.

No external calendar integration is required for the MVP. Use local display only.

### 13. Exam Grader

Implement a practice grader:

Inputs:

- subject;
- question;
- student answer;
- maximum points;
- optional marking scheme;
- retrieved criteria/notes.

Outputs:

- points achieved;
- grade using `grade = points_achieved / maximum_points * 5 + 1`;
- strengths;
- missing points;
- improved answer;
- warning that this is practice feedback, not an official grade.

Validation:

- maximum points must be positive;
- points achieved must be between 0 and maximum points;
- grade should be rounded reasonably.

### 14. Feedback Loop

Implement local feedback storage.

Store feedback in JSONL or CSV with:

- timestamp;
- subject;
- feature;
- user question/task;
- app answer;
- rating;
- free-text feedback;
- source chunk IDs if available.

Do not train a model. Use feedback to help improve prompts and material coverage manually.

### 15. Stats and Planner Placeholders

Implement simple local placeholders for:

- grades table;
- average grade;
- upcoming exam list;
- simple to-do list;
- desired grade calculation.

Do not implement Google Calendar integration yet. Add TODO comments explaining future extension points.

## Code Quality Requirements

- Every module must have a top-level docstring explaining its purpose.
- Every function must have a docstring explaining inputs, outputs, and behavior.
- Add clear comments for important lines because a 15-year-old student will read this code.
- Keep functions small.
- Avoid long prompt strings inside `app.py`; store prompts in `src/prompts.py`.
- Avoid app logic inside the UI where possible; UI should call functions from `src/`.
- Add type hints where simple and helpful.
- Add defensive handling for missing folders, missing material, empty vector DB, and missing Ollama connection.

## Acceptance Criteria

The app is acceptable when:

- `streamlit run app.py` starts the local app.
- A user can select a subject and language.
- A user can index or load subject material.
- A user can ask a question and receive an answer grounded in retrieved sources.
- A user can generate a quiz.
- A user can generate a mock exam.
- A user can generate a study plan.
- A user can grade a practice answer.
- Feedback can be saved locally.
- The code is modular and documented.
- The default LLM path is local Ollama with DeepSeek Distilled or another configured local model.


---

# File: 02_codex_testing_prompt.md

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


---

# File: 03_codex_readme_run_app_prompt.md

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


# Codex Prompt 3: Create README for Installing and Starting the App in Linux Shell

## Your Task

Create or update a README file explaining how to install, configure, and start the locally hosted **Alim Study Assistant** app from a Linux shell.

The README should be written for a beginner student and mentor. It must be clear, step-by-step, and not assume advanced Linux knowledge.

Suggested output file:

```text
README_RUN_APP.md
```

If the repo already has a README, either update it carefully or create this separate README file.

## Required Sections

### 1. What You Need Before Starting

Explain that the user needs:

- Linux shell or VS Code Remote-SSH terminal.
- Conda installed.
- Git installed.
- Ollama installed separately.
- A local DeepSeek Distilled model pulled in Ollama.
- The repository cloned locally or opened on the remote machine.

### 2. Create the Conda Environment

Document commands:

```bash
conda env create -f environment.yml
conda activate alim-study-assistant
```

If `environment.yml` is not available, include fallback:

```bash
conda create -n alim-study-assistant python=3.11
conda activate alim-study-assistant
pip install -r requirements.txt
```

Explain what each command does in simple language.

### 3. Install or Check Ollama

Document how to check if Ollama is running:

```bash
ollama --version
ollama list
```

Explain that Ollama itself is not installed by Python packages and must be installed as a separate local application/runtime.

### 4. Pull or Confirm the Local Model

Document that the model name depends on the machine and available VRAM/RAM.

Example placeholder:

```bash
ollama pull <deepseek-distilled-model-name>
```

Explain that the model should be chosen so it stays within roughly 16 GB VRAM occupancy max.

### 5. Configure `.env`

Document:

```bash
cp .env.example .env
```

Example `.env` content:

```env
MODEL_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=<deepseek-distilled-model-name>
CHROMA_DB_DIR=vector_db
```

Explain that `.env` should not be committed to GitHub.

### 6. Start the App

Document:

```bash
streamlit run app.py
```

Explain that the app should open at a local URL similar to:

```text
http://localhost:8501
```

### 7. Add Subject Material

Explain where to put files:

```text
data/subjects/<subject_key>/notes/
data/subjects/<subject_key>/syllabus/
data/subjects/<subject_key>/criteria/
```

Explain that the app should support syllabus, notes, and criteria in:

- DOCX
- PDF
- MD
- TXT

### 8. Build or Rebuild Subject Database

Document how to use the app UI or command-line script, depending on implementation, to index subject material into Chroma.

If there is a CLI script, document it. If not, explain through the Streamlit UI.

### 9. Troubleshooting

Include common problems:

- Conda environment not activated.
- Package import error.
- Ollama not running.
- Model not found.
- Chroma/vector DB missing.
- No subject notes found.
- Port already in use.

### 10. Safety and Privacy Notes

Explain:

- This is a local educational app.
- It is not an official grading system.
- It should not be used for medical/legal advice.
- Private `.env` and private notes should not be pushed to GitHub.

## Style Requirements

- Use simple language.
- Include shell commands in fenced code blocks.
- Explain what important commands do.
- Keep commands copy-pasteable.
- Keep the README modular and traceable.


---

# File: 04_codex_readme_testing_prompt.md

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


---

# File: 05_codex_readme_app_description_prompt.md

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


# Codex Prompt 5: Create README Describing What the App Does

## Your Task

Create or update a README that describes the **Alim Study Assistant** app, what it does, who it is for, how it works, and what features it includes.

Suggested output file:

```text
README_APP_DESCRIPTION.md
```

This README should be understandable to:

- the student;
- the mentor;
- parents/teachers;
- future developers reviewing the project.

## Required Sections

### 1. Project Title

Use:

```text
Alim Study Assistant
```

### 2. Short Description

Explain that this is a locally hosted AI exam-preparation web app that helps organize school subjects, notes, learning goals, quizzes, mock exams, study plans, and practice grading.

### 3. Who It Is For

Explain:

- It is built for a student preparing for exams.
- It is also a learning project to teach Python, local AI, RAG, testing, and software architecture.
- It is not a replacement for teachers or official grading.

### 4. Main Features

Describe:

- Separate subject chatbot behavior.
- Separate local vector database per subject.
- Notes, syllabus, learning goals, and criteria ingestion.
- DOCX, PDF, MD, and TXT support where implemented.
- Subject-specific retrieval.
- Quiz generation.
- Mock exam generation.
- Study plan generation.
- Practice answer grading.
- German and English behavior.
- Feedback collection.
- Basic stats/planner placeholders.

### 5. Supported Subjects

List the supported subject categories and their intended behavior:

- SPF Chemistry.
- SPF Biology.
- Political Education.
- Philosophy.
- Pedagogics/Psychology.
- Maths/Physics.
- History.
- German.
- French.
- English.
- Chemistry.

### 6. How the App Works

Explain the pipeline in simple terms:

```text
User selects subject and task
→ app retrieves relevant subject notes/syllabus/criteria
→ app sends only relevant context to the local LLM
→ local LLM generates an answer, quiz, exam, plan, or feedback
→ app shows answer and sources
→ user can give feedback
```

### 7. Local AI / Privacy

Explain:

- The app defaults to local Ollama.
- The model is a locally hosted DeepSeek Distilled model or another configured local model.
- Private school material should remain local.
- `.env`, private notes, and vector DB files should not be committed to GitHub.

### 8. Grading Disclaimer

Explain:

- The grader is for practice feedback only.
- It uses a point-based formula where applicable:

```text
grade = points_achieved / maximum_points * 5 + 1
```

- It does not produce official school grades.

### 9. Educational Purpose

Explain what the student learns by building it:

- Python.
- Streamlit.
- Linux/Git.
- Document processing.
- Embeddings.
- Vector search.
- Local LLMs.
- Prompting.
- RAG.
- Testing.
- Responsible AI.

### 10. Current MVP and Future Ideas

Describe MVP features and later ideas:

MVP:

- Local app.
- Subject selection.
- Material ingestion.
- Retrieval and LLM answers.
- Quiz/mock exam/study plan/grader.

Future:

- Better UI.
- Google Calendar import.
- Better charts/stats.
- More robust image handling.
- Better molecule rendering.
- More advanced feedback analysis.

## Style Requirements

- Use clear headings.
- Use bullet points.
- Keep tone friendly and professional.
- Avoid overclaiming model accuracy.
- Emphasize local-first, modular, traceable design.
