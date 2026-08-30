"""In-app documentation page for students."""

from __future__ import annotations

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    st = None


def render_help_page(config) -> None:
    """Render simple in-app documentation."""
    if st is None:
        return
    st.header("Help")
    st.write("Register or log in first. Each account has separate notes, chat history, media, quizzes, exams, and reports.")
    st.write("Choose a subject in the sidebar, then use the dashboard, chatbot, quiz mode, or exam mode.")
    st.write("Images and audio are processed locally. If OCR, Whisper, Ollama, or internet tools are missing, the app shows a warning instead of crashing.")
    st.write("Quiz and exam solutions are stored locally but hidden until you submit answers and grading is finished.")
    st.write("The app estimates prompt size and trims lower-priority context before reaching the 128K local Gemma limit.")
    st.code("ollama pull gemma3:4b\npython scripts/verify_environment.py\nstreamlit run app.py")
