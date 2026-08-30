"""Subject dashboard page helpers."""

from __future__ import annotations

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    st = None

from .adaptive_learning import recommend_study_actions, suggest_focus_topics
from .ui_components import action_card


def render_subject_dashboard(subject, config, user_id: str) -> None:
    """Render a compact subject dashboard."""
    if st is None:
        return
    st.header(f"{subject.display_name} Dashboard")
    cols = st.columns(2)
    with cols[0]:
        action_card("Generate Quiz Set", "Use Quiz Mode for timed practice with hidden solutions.")
    with cols[1]:
        action_card("Generate Exam Question Set", "Use Exam Mode for a longer timed attempt.")
    st.subheader("Focus")
    topics = suggest_focus_topics(subject.key, config)
    st.write(", ".join(topics) if topics else "No weak topics recorded yet.")
    for action in recommend_study_actions(subject.key, config):
        st.caption(action)
