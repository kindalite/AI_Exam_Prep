# Multimodal, Web, Syllabus, and Memory

Learning material root: `/home/kindalite/AI-App/AI_Exam_Prep/learning_material`.

PDF ingestion can use selectable text, rendered page OCR, and local `gemma3:4b` image descriptions. Missing PyMuPDF, Tesseract, Whisper, internet, or Ollama features produce warnings instead of crashes.

Official KSA/Lucerne syllabus sources are cached under `data/web_cache/syllabus`. Public web retrieval is optional and uses public-safe queries when private-query web use is disabled.

Chat prompts, image/audio metadata, transcripts, OCR text, generated practice, submitted answers, grading reports, and performance recommendations are stored per user and can be indexed into RAG memory.
