# Alim Study Assistant

## Short Description

Alim Study Assistant is a locally hosted AI exam-preparation web app. It helps organize school subjects, notes, learning goals, quizzes, mock exams, study plans, and practice grading.

## Who It Is For

- A student preparing for exams.
- A mentor or parent helping keep learning material organized.
- Future developers reviewing a simple Python, Streamlit, RAG, local AI, and testing project.

It is not a replacement for teachers or official grading.

## Main Features

- Separate subject chatbot behavior.
- Separate local vector database per subject.
- Notes, syllabus, learning goals, and criteria ingestion.
- DOCX, PDF, MD, and TXT support where installed packages allow it.
- Subject-specific retrieval.
- Quiz generation.
- Mock exam generation.
- Study plan generation.
- Practice answer grading.
- German, English, and simple French behavior.
- Local feedback collection.
- Basic stats and planner placeholders.

## Supported Subjects

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

## How the App Works

```text
User selects subject and task
-> app retrieves relevant subject notes/syllabus/criteria
-> app sends only relevant context to the local LLM
-> local LLM generates an answer, quiz, exam, plan, or feedback
-> app shows answer and sources
-> user can give feedback
```

## Local AI and Privacy

The app defaults to local Ollama. The model can be a locally hosted DeepSeek Distilled model or another configured local model.

Private school material should remain local. Do not commit `.env`, private notes, or vector database files to GitHub.

## Grading Disclaimer

The grader gives practice feedback only. Where point-based grading is used, it follows:

```text
grade = points_achieved / maximum_points * 5 + 1
```

It does not produce official school grades.

## Educational Purpose

Building this app helps teach:

- Python.
- Streamlit.
- Linux and Git.
- Document processing.
- Embeddings.
- Vector search.
- Local LLMs.
- Prompting.
- RAG.
- Testing.
- Responsible AI.

## Current MVP and Future Ideas

MVP:

- Local app.
- Subject selection.
- Material ingestion.
- Retrieval and LLM answers.
- Quiz, mock exam, study plan, and grader.

Future:

- Better UI.
- Google Calendar import.
- Better charts and stats.
- More robust image handling.
- Better molecule rendering.
- More advanced feedback analysis.

