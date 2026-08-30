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
