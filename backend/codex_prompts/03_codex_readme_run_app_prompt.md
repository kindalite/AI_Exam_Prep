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
