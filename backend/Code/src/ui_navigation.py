"""Navigation labels for the Streamlit app."""

from __future__ import annotations

PAGES = ["Home", "Subject Dashboard", "Subject Chatbot", "Quiz Mode", "Exam Mode", "Learning Goals", "Study Plan", "Exam Grader", "Notes Ingestion", "Feedback", "Stats Planner", "Help"]


def page_labels() -> list[str]:
    """Return the main navigation page labels."""
    return list(PAGES)
