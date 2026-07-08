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
- `.one`

The app must be able to ingest and index these formats where feasible. Use clear source metadata so retrieved answers can show where information came from.

## Subject Criteria to Support

Build the app so each subject can have its own criteria file and subject-specific behavior. Include at least these subjects and criteria assumptions:

SPF - stands for German "Schwerpunktfach" which means "focus subject" 

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
follow the official Swiss grading system

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
