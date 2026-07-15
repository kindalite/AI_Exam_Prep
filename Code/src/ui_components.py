"""Small Streamlit UI components shared across pages."""

from __future__ import annotations

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    st = None


def status_card(title: str, body: str, color: str = "#e0f2fe") -> None:
    """Render a simple colorful status card."""
    if st is None:
        return
    st.markdown(f"<div style='background:{color};padding:1rem;border-radius:8px;margin:.5rem 0'><strong>{title}</strong><br>{body}</div>", unsafe_allow_html=True)


def action_card(title: str, body: str) -> None:
    """Render a beginner-friendly action card."""
    status_card(title, body, "#ecfccb")
