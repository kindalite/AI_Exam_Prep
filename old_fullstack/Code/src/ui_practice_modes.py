"""Streamlit UI for timed quiz and exam modes."""

from __future__ import annotations

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    st = None

from .adaptive_learning import choose_adaptive_difficulty
from .exam_mode import generate_exam_set, start_exam_mode
from .quiz_mode import generate_quiz_set, start_quiz_mode
from .timed_practice import submit_and_grade_attempt


def render_quiz_mode(user_id: str, subject, language: str, config) -> None:
    """Render focused quiz mode."""
    _render_mode("quiz", user_id, subject, language, config)


def render_exam_mode(user_id: str, subject, language: str, config) -> None:
    """Render focused exam mode."""
    _render_mode("exam", user_id, subject, language, config)


def _render_mode(mode: str, user_id: str, subject, language: str, config) -> None:
    """Render setup/running/submission controls for one practice mode."""
    if st is None:
        return
    title = "Quiz Mode" if mode == "quiz" else "Exam Mode"
    st.header(title)
    topic = st.text_input("Topic or learning goal", key=f"{mode}_topic")
    difficulty = st.selectbox("Difficulty", ["adaptive", "easy", "medium", "hard"], key=f"{mode}_difficulty")
    timer = st.number_input("Timer duration in minutes", min_value=1, value=config.default_quiz_timer_minutes if mode == "quiz" else config.default_exam_timer_minutes, key=f"{mode}_timer")
    count_or_points = st.number_input("Questions" if mode == "quiz" else "Total points", min_value=1, value=5 if mode == "quiz" else 50, key=f"{mode}_count_points")
    st.checkbox("Use official syllabus if local material is missing", value=True, key=f"{mode}_syllabus")
    st.checkbox("Use internet/public web sources", value=False, key=f"{mode}_web")
    state_key = f"{mode}_session"
    if st.button(f"Start {title}"):
        used = choose_adaptive_difficulty(subject.key, topic, config) if difficulty == "adaptive" else difficulty
        if mode == "quiz":
            response = generate_quiz_set(subject, language, topic, difficulty, int(count_or_points), call_llm=False)
            session, practice, _solution = start_quiz_mode(user_id, subject, language, topic, difficulty, used, int(timer), response.text, config)
        else:
            response = generate_exam_set(subject, language, int(count_or_points), difficulty, call_llm=False)
            session, practice, _solution = start_exam_mode(user_id, subject, language, topic, difficulty, used, int(timer), response.text, config)
        st.session_state[state_key] = session
        st.session_state[f"{mode}_questions"] = practice["question_set"]
    session = st.session_state.get(state_key)
    if session:
        st.info(f"Attempt status: {session.status}. Solutions stay hidden until grading is finished.")
        st.text_area("Questions", value=st.session_state.get(f"{mode}_questions", ""), height=240, disabled=True)
        answers = st.text_area("Your answers", key=f"{mode}_answers")
        points = st.number_input("Points achieved after review", min_value=0.0, value=0.0, key=f"{mode}_points")
        maximum = st.number_input("Maximum points", min_value=1.0, value=10.0 if mode == "quiz" else float(count_or_points), key=f"{mode}_maximum")
        if st.button(f"Submit and grade {title}"):
            result = submit_and_grade_attempt(session, answers, float(points), float(maximum), ["Submitted practice"], ["Review missed items"], ["Repeat weak topics"], config)
            st.session_state[state_key] = result["session"]
            st.success(f"Grade: {result['grade']}. Solutions are now visible: {result['solutions_visible']}")
