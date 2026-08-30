# Architecture

The app is a local Streamlit application under `Code/`.

Core layers:

- `src/config.py`: environment and runtime settings.
- `src/auth.py`, `src/user_manager.py`, `src/user_data_paths.py`: local accounts and isolated folders.
- `src/document_loaders.py`, `src/multimodal_pdf.py`, `src/ocr.py`, `src/image_understanding.py`, `src/audio_transcription.py`: local material and multimodal processing.
- `src/retrieval.py`, `src/vector_store.py`, `src/rag_memory_indexer.py`: subject and memory retrieval.
- `src/token_budget.py`: conservative 128K prompt budget enforcement.
- `src/quiz_mode.py`, `src/exam_mode.py`, `src/timed_practice.py`, `src/attempt_session.py`: timed practice flows.
- `src/practice_store.py`, `src/chat_history_store.py`, `src/performance_tracker.py`: local memory and reports.
- `src/ui_*.py`: Streamlit UI sections.

Source priority for prompts keeps current user input first, then teacher/user material, learning goals, official syllabus, performance memory, generated practice/history, public web, and general instructions.
