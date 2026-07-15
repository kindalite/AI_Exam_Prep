# App Description

Alim Study Assistant helps students study with local notes, OneNote PDFs, image/audio inputs, syllabus fallback, timed quizzes, timed exams, grading, and adaptive memory.

The first screen is login/register. Passwords are salted and hashed locally. Each user has isolated chat history, media, practice sets, hidden solutions, attempts, reports, and RAG exports.

Quiz Mode and Exam Mode save question sets and hidden solution sets. Solutions are shown only after answers are submitted and grading is complete.

The prompt system enforces a conservative 128K token safety limit before calling local Ollama `gemma3:4b`.
