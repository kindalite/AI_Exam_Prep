"""Streamlit UI for the local Alim Study Assistant web app."""

from __future__ import annotations

from datetime import date
from pathlib import Path

try:
    import streamlit as st
except ImportError:  # Keeps smoke imports working before Streamlit is installed.
    st = None

from src.config import load_config
from src.feedback import save_feedback
from src.grader import calculate_grade, create_grading_feedback
from src.llm_client import generate_response
from src.mock_exam_generator import create_mock_exam
from src.prompts import build_chat_prompt, build_system_prompt
from src.quiz_generator import create_quiz
from src.retrieval import build_subject_index, load_exam_criteria, load_learning_goals, retrieve_for_subject
from src.stats import average_grade, desired_grade_points, grade_table, practice_grade_row
from src.study_plan_generator import create_study_plan
from src.subject_registry import setup_subject_folders, subjects_for_display


def _require_streamlit() -> None:
    """Show a clear message when the app is run without Streamlit installed."""
    if st is None:
        raise RuntimeError("Streamlit is not installed. Run: pip install -r requirements.txt")


def _selected_subject():
    """Read the selected subject and language from the sidebar."""
    config = load_config()
    subjects = subjects_for_display(config)
    subject_names = [subject.display_name for subject in subjects]
    selected_name = st.sidebar.selectbox("Subject", subject_names)
    subject = next(item for item in subjects if item.display_name == selected_name)
    language = st.sidebar.selectbox("Language", ["German", "English", "French"], index=["German", "English", "French"].index(subject.default_language if subject.default_language in ["German", "English", "French"] else "German"))
    return config, subject, language


def render_home() -> None:
    """Render the home page."""
    st.title("Alim Study Assistant")
    st.write("Local exam preparation with subject folders, retrieval, quizzes, mock exams, planning, grading, and feedback.")
    st.info("Add notes under data/subjects/<subject_key>/notes, then use the ingestion page to build a local subject database.")


def render_ingestion(subject, config) -> None:
    """Render material ingestion controls."""
    st.header("Notes and Material Ingestion")
    st.write(f"Notes folder: `{subject.notes_dir}`")
    uploaded_files = st.file_uploader("Add MD, TXT, PDF, or DOCX material", accept_multiple_files=True, type=["md", "txt", "pdf", "docx"])
    if uploaded_files:
        subject.notes_dir.mkdir(parents=True, exist_ok=True)
        for uploaded_file in uploaded_files:
            target = subject.notes_dir / uploaded_file.name
            target.write_bytes(uploaded_file.getbuffer())
        st.success(f"Saved {len(uploaded_files)} file(s).")
    if st.button("Build or rebuild subject database"):
        count = build_subject_index(subject, config)
        st.success(f"Indexed {count} chunks for {subject.display_name}.")


def render_chat(subject, language) -> None:
    """Render the subject chatbot."""
    st.header("Subject Chatbot")
    question = st.text_area("Question", placeholder="Ask about current notes, syllabus, learning goals, or criteria.")
    if st.button("Ask") and question.strip():
        retrieved = retrieve_for_subject(subject, question)
        prompt = build_chat_prompt(
            subject,
            language,
            question,
            retrieved.context,
            load_learning_goals(subject),
            load_exam_criteria(subject),
        )
        response = generate_response(prompt, build_system_prompt(subject, language))
        if response.ok:
            st.markdown(response.text)
        else:
            st.warning(response.error)
            st.code(prompt)
        if retrieved.sources:
            st.subheader("Sources")
            for source in retrieved.sources:
                st.caption(f"{source.metadata.get('source_name', 'source')} - score {source.score:.2f}")


def render_learning_goals(subject) -> None:
    """Show learning goals and relevant retrieved material."""
    st.header("Learning Goals")
    goals = load_learning_goals(subject)
    st.text_area("Stored learning goals", value=goals, height=220)
    selected_goal = st.text_input("Paste or select a learning goal to connect with notes")
    if st.button("Find relevant material") and selected_goal:
        retrieved = retrieve_for_subject(subject, selected_goal)
        st.write(retrieved.message)
        st.text(retrieved.context or "No source context found yet.")


def render_quiz(subject, language) -> None:
    """Render quiz generation controls."""
    st.header("Quiz Generator")
    learning_goal = st.text_input("Learning goal or topic")
    difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
    if st.button("Generate quiz"):
        response = create_quiz(subject, language, learning_goal, difficulty)
        st.markdown(response.text if response.ok else response.error)


def render_mock_exam(subject, language) -> None:
    """Render mock exam generation controls."""
    st.header("Mock Exam Generator")
    total_points = st.number_input("Total points", min_value=1, value=50)
    difficulty = st.selectbox("Exam difficulty", ["easy", "medium", "hard"])
    if st.button("Generate mock exam"):
        response = create_mock_exam(subject, language, int(total_points), difficulty)
        st.markdown(response.text if response.ok else response.error)


def render_study_plan(subject, language) -> None:
    """Render study plan generation controls."""
    st.header("Study Plan Generator")
    exam_date = st.date_input("Exam date", value=date.today())
    hours = st.number_input("Available hours per week", min_value=0.5, value=4.0, step=0.5)
    weak_topics = st.text_area("Weak topics")
    if st.button("Generate study plan"):
        response = create_study_plan(subject, language, str(exam_date), float(hours), weak_topics)
        st.markdown(response.text if response.ok else response.error)


def render_grader(subject, language) -> None:
    """Render the practice grader."""
    st.header("Practice Exam Grader")
    question = st.text_area("Question")
    answer = st.text_area("Student answer")
    max_points = st.number_input("Maximum points", min_value=1.0, value=10.0)
    achieved = st.number_input("Manual points achieved for formula check", min_value=0.0, max_value=float(max_points), value=0.0)
    st.write(f"Formula grade: {calculate_grade(float(achieved), float(max_points)).grade}")
    marking_scheme = st.text_area("Optional marking scheme")
    if st.button("Ask AI for practice feedback"):
        response = create_grading_feedback(subject, language, question, answer, float(max_points), marking_scheme)
        st.markdown(response.text if response.ok else response.error)


def render_feedback(subject) -> None:
    """Render local feedback storage controls."""
    st.header("Feedback")
    feature = st.selectbox("Feature", ["chat", "quiz", "mock_exam", "study_plan", "grader", "ingestion"])
    task = st.text_area("What did you ask the app to do?")
    answer = st.text_area("What answer did the app give?")
    rating = st.slider("Rating", min_value=1, max_value=5, value=3)
    comment = st.text_area("Comment")
    if st.button("Save feedback"):
        save_feedback(subject.key, feature, task, answer, rating, comment)
        st.success("Feedback saved locally.")


def render_stats() -> None:
    """Render simple stats and planner placeholders."""
    st.header("Stats and Planner")
    st.caption("Calendar integration is a future extension; this MVP keeps planner data local.")
    sample_rows = [
        practice_grade_row("Biology", 8, 10, str(date.today())),
        practice_grade_row("History", 14, 20, str(date.today())),
    ]
    table = grade_table(sample_rows)
    st.dataframe(table, use_container_width=True)
    st.write(f"Average grade: {average_grade(table['grade'].tolist())}")
    desired = st.number_input("Desired grade", min_value=1.0, max_value=6.0, value=5.0)
    maximum = st.number_input("Maximum points for target exam", min_value=1.0, value=50.0)
    st.write(f"Points needed: {desired_grade_points(float(desired), float(maximum))}")
    st.checkbox("TODO: Add upcoming exam")
    st.checkbox("TODO: Add revision task")


def main() -> None:
    """Run the Streamlit application."""
    _require_streamlit()
    config = load_config(Path(__file__).resolve().parent)
    setup_subject_folders(config)
    st.set_page_config(page_title="Alim Study Assistant", layout="wide")
    st.markdown("<style>:root{--primary-color:#2563eb;} .stButton button{border-radius:6px;}</style>", unsafe_allow_html=True)
    config, subject, language = _selected_subject()
    page = st.sidebar.radio(
        "Main menu",
        ["Home", "Subject Chatbot", "Learning Goals", "Quiz Generator", "Mock Exam", "Study Plan", "Exam Grader", "Notes Ingestion", "Feedback", "Stats Planner"],
    )
    if page == "Home":
        render_home()
    elif page == "Subject Chatbot":
        render_chat(subject, language)
    elif page == "Learning Goals":
        render_learning_goals(subject)
    elif page == "Quiz Generator":
        render_quiz(subject, language)
    elif page == "Mock Exam":
        render_mock_exam(subject, language)
    elif page == "Study Plan":
        render_study_plan(subject, language)
    elif page == "Exam Grader":
        render_grader(subject, language)
    elif page == "Notes Ingestion":
        render_ingestion(subject, config)
    elif page == "Feedback":
        render_feedback(subject)
    else:
        render_stats()


if __name__ == "__main__":
    main()

