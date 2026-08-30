"""Streamlit UI for the local Alim Study Assistant web app."""

from __future__ import annotations

from datetime import date
from pathlib import Path

try:
    import streamlit as st
except ImportError:  # Keeps smoke imports working before Streamlit is installed.
    st = None

from src.config import load_config
from src.app_logging import append_log, new_app_run_log, new_user_session_log
from src.services.chat_service import run_chat
from src.services.feedback_service import submit_feedback
from src.services.grading_service import calculate_swiss_grade, generate_grading_feedback, save_grading_attempt
from src.services.health_service import get_model_status, warm_model_runtime
from src.services.material_service import discover_material, fetch_subject_syllabus, rebuild_subject_index, save_uploaded_material
from src.services.mock_exam_service import generate_mock_exam
from src.services.quiz_service import generate_quiz
from src.services.study_plan_service import generate_study_plan
from src.services.subject_service import find_relevant_material, list_subjects, performance_summary, read_learning_goals, recent_attempts
from src.stats import average_grade, desired_grade_points, grade_table, practice_grade_row
from src.subject_languages import language_for_subject
from src.subject_registry import setup_subject_folders
from src.ui_auth import require_login
from src.ui_docs import render_help_page
from src.ui_navigation import page_labels
from src.ui_practice_modes import render_exam_mode as render_focused_exam_mode, render_quiz_mode as render_focused_quiz_mode
from src.ui_subject_dashboard import render_subject_dashboard


def _require_streamlit() -> None:
    """Show a clear message when the app is run without Streamlit installed."""
    if st is None:
        raise RuntimeError("Streamlit is not installed. Run: pip install -r requirements.txt")


def _selected_subject():
    """Read the selected subject and language from the sidebar."""
    config = load_config(Path(__file__).resolve().parent)
    subjects = list_subjects(config)
    subject_names = [subject.display_name for subject in subjects]
    selected_name = st.sidebar.selectbox("Subject", subject_names)
    subject = next(item for item in subjects if item.display_name == selected_name)
    language = language_for_subject(subject.key, subject.default_language)
    st.sidebar.caption(f"Response language: {language} (automatic for {subject.display_name})")
    st.sidebar.caption(f"Local model: {config.ollama_model}")
    return config, subject, language


def render_home() -> None:
    """Render the home page."""
    st.title("Alim’s Study Assistant")
    st.write("Local exam preparation with retrieval, quizzes, mock exams, planning, grading, multimodal inputs, syllabus fallback, and adaptive practice memory.")
    st.info("Private notes, images, and audio stay local. Public web retrieval is only used when you enable it.")


def render_model_runtime_panel(config) -> None:
    """Show local model status and optional warm-up control."""
    status = get_model_status(config)
    if status.ok:
        st.success(status.message)
    else:
        st.warning(status.message)
    if st.button("Warm local model"):
        with st.spinner("Warming the local model..."):
            warmed = warm_model_runtime(config)
        st.success(warmed.message) if warmed.ok else st.warning(warmed.message)


def render_ingestion(subject, config) -> None:
    """Render material ingestion controls."""
    st.header("Notes and Material Ingestion")
    st.write(f"Subject notes folder: `{subject.notes_dir}`")
    st.write(f"External learning material root: `{config.learning_material_root}`")
    st.write("Root exists." if config.learning_material_root and config.learning_material_root.exists() else "Root not found yet.")

    uploaded_files = st.file_uploader("Add MD, TXT, PDF, DOCX, PNG, or JPG material", accept_multiple_files=True, type=["md", "txt", "pdf", "docx", "png", "jpg", "jpeg", "svg"])
    if uploaded_files:
        subject.notes_dir.mkdir(parents=True, exist_ok=True)
        for uploaded_file in uploaded_files:
            save_uploaded_material(uploaded_file.getbuffer(), uploaded_file.name, subject)
        st.success(f"Saved {len(uploaded_files)} file(s).")

    grouped = discover_material(config)
    st.subheader("Discovered external material")
    if grouped:
        for key, files in grouped.items():
            st.caption(f"{key}: {len(files)} file(s)")
            for path in files[:8]:
                st.text(str(path))
    else:
        st.caption("No external supported files discovered yet.")

    if st.button("Fetch/cache official KSA/Lucerne syllabus for this subject"):
        with st.spinner("Fetching and caching the official syllabus..."):
            docs = fetch_subject_syllabus(subject, config)
        st.success(f"Cached {len(docs)} syllabus document(s) for {subject.display_name}.")
    if st.button("Build or rebuild subject database"):
        with st.spinner("Indexing subject material..."):
            count = rebuild_subject_index(subject, config)
        st.success(f"Indexed {count} chunks for {subject.display_name}.")


def render_chat(subject, language, config, user_id: str) -> None:
    """Render the subject chatbot."""
    st.header("Subject Chatbot")
    question = st.text_area("Question", placeholder="Ask about current notes, syllabus, learning goals, criteria, or an uploaded image/audio file.")
    image_file = st.file_uploader("Optional image or screenshot", type=["png", "jpg", "jpeg"])
    audio_file = st.file_uploader("Optional audio question", type=["wav", "mp3", "m4a", "ogg"])
    use_syllabus = st.checkbox("Use official syllabus if local material is missing", value=True)
    use_web = st.checkbox("Use internet/public web sources", value=False)

    if st.button("Ask") and (question.strip() or image_file or audio_file):
        with st.spinner("Retrieving sources and generating a grounded answer..."):
            result = run_chat(
                subject=subject,
                language=language,
                question=question,
                user_id=user_id,
                config=config,
                image_bytes=image_file.getbuffer() if image_file else None,
                image_name=image_file.name if image_file else None,
                audio_bytes=audio_file.getbuffer() if audio_file else None,
                audio_name=audio_file.name if audio_file else None,
                include_syllabus=use_syllabus,
                include_web=use_web,
            )
        if result.image_ocr:
            st.text_area("Image OCR", value=result.image_ocr, height=120)
        if result.image_description:
            st.text_area("Image description", value=result.image_description, height=120)
        if result.audio_transcript:
            st.text_area("Audio transcript", value=result.audio_transcript, height=120)
        if result.response.ok:
            st.markdown(result.response.text)
        else:
            st.warning(result.response.error)
            st.code(result.prompt)
        if result.warnings:
            st.subheader("Warnings")
            for warning in result.warnings:
                st.warning(warning)
        if result.context.sources:
            st.subheader("Sources")
            for source in result.context.sources:
                layer = source.metadata.get("source_layer", "local_material")
                name = source.metadata.get("source_name", "source")
                page = source.metadata.get("page_number", "")
                modality = source.metadata.get("modality", "")
                url = source.metadata.get("url", "")
                st.caption(f"{layer}: {name} {f'page {page}' if page else ''} {modality} {url}")


def render_learning_goals(subject) -> None:
    """Show learning goals and relevant retrieved material."""
    st.header("Learning Goals")
    goals = read_learning_goals(subject)
    st.text_area("Stored learning goals", value=goals, height=220)
    selected_goal = st.text_input("Paste or select a learning goal to connect with notes")
    if st.button("Find relevant material") and selected_goal:
        context = find_relevant_material(subject, selected_goal)
        st.text(context.context or "No source context found yet.")


def render_quiz(subject, language) -> None:
    """Render quiz generation controls."""
    st.header("Quiz Generator")
    learning_goal = st.text_input("Learning goal or topic")
    difficulty = st.selectbox("Difficulty", ["adaptive", "easy", "medium", "hard"])
    if st.button("Generate quiz"):
        response = generate_quiz(subject, language, learning_goal, difficulty)
        st.markdown(response.text if response.ok else response.error)


def render_mock_exam(subject, language) -> None:
    """Render mock exam generation controls."""
    st.header("Mock Exam Generator")
    total_points = st.number_input("Total points", min_value=1, value=50)
    difficulty = st.selectbox("Exam difficulty", ["adaptive", "easy", "medium", "hard"])
    if st.button("Generate mock exam"):
        response = generate_mock_exam(subject, language, int(total_points), difficulty)
        st.markdown(response.text if response.ok else response.error)


def render_study_plan(subject, language) -> None:
    """Render study plan generation controls."""
    st.header("Study Plan Generator")
    exam_date = st.date_input("Exam date", value=date.today())
    hours = st.number_input("Available hours per week", min_value=0.5, value=4.0, step=0.5)
    weak_topics = st.text_area("Weak topics")
    if st.button("Generate study plan"):
        response = generate_study_plan(subject, language, str(exam_date), float(hours), weak_topics)
        st.markdown(response.text if response.ok else response.error)


def render_grader(subject, language, config) -> None:
    """Render the practice grader."""
    st.header("Practice Exam Grader")
    question = st.text_area("Question")
    answer = st.text_area("Student answer")
    max_points = st.number_input("Maximum points", min_value=1.0, value=10.0)
    achieved = st.number_input("Manual points achieved for formula check", min_value=0.0, max_value=float(max_points), value=0.0)
    result = calculate_swiss_grade(float(achieved), float(max_points))
    st.write(f"Formula grade: {result.grade}")
    marking_scheme = st.text_area("Optional marking scheme")
    if st.button("Ask AI for practice feedback"):
        response = generate_grading_feedback(subject, language, question, answer, float(max_points), marking_scheme)
        st.markdown(response.text if response.ok else response.error)
    if st.button("Save this manual grade to performance memory"):
        save_grading_attempt(subject, question, answer, "Manual grade saved from grader page.", float(achieved), float(max_points), config)
        st.success("Practice attempt saved locally.")


def render_feedback(subject) -> None:
    """Render local feedback storage controls."""
    st.header("Feedback")
    feature = st.selectbox("Feature", ["chat", "quiz", "mock_exam", "study_plan", "grader", "ingestion"])
    task = st.text_area("What did you ask the app to do?")
    answer = st.text_area("What answer did the app give?")
    rating = st.slider("Rating", min_value=1, max_value=5, value=3)
    comment = st.text_area("Comment")
    if st.button("Save feedback"):
        submit_feedback(subject_key=subject.key, feature=feature, user_task=task, app_answer=answer, rating=rating, comment=comment)
        st.success("Feedback saved locally.")


def render_stats(subject, config) -> None:
    """Render performance stats and planner placeholders."""
    st.header("Stats and Planner")
    summary = performance_summary(subject, config)
    st.write(f"Next recommended difficulty: {summary['next_difficulty']}")
    st.write("Recommended actions:")
    for action in summary["recommended_actions"]:
        st.caption(action)
    table = recent_attempts(subject, config)
    if not table.empty:
        st.dataframe(table, use_container_width=True)
    else:
        sample_rows = [practice_grade_row("Biology", 8, 10, str(date.today())), practice_grade_row("History", 14, 20, str(date.today()))]
        sample_table = grade_table(sample_rows)
        st.dataframe(sample_table, use_container_width=True)
        st.write(f"Sample average grade: {average_grade(sample_table['grade'].tolist())}")
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
    st.set_page_config(page_title="Alim’s Study Assistant", layout="wide")
    st.markdown("<style>:root{--primary-color:#2563eb;} .stButton button{border-radius:6px;} section[data-testid=stSidebar]{background:#eff6ff;}</style>", unsafe_allow_html=True)
    user = require_login(config)
    if user is None:
        return
    user_id = user["user_id"]
    if "app_run_log" not in st.session_state:
        st.session_state["app_run_log"] = str(new_app_run_log(config))
        append_log(Path(st.session_state["app_run_log"]), "app_started", {"model": config.ollama_model})
    if "user_session_log" not in st.session_state:
        st.session_state["user_session_log"] = str(new_user_session_log(config, user_id))
        append_log(Path(st.session_state["user_session_log"]), "user_session_started", {"user_id": user_id})
    render_model_runtime_panel(config)
    config, subject, language = _selected_subject()
    page = st.sidebar.radio("Main menu", page_labels())
    if page == "Home":
        render_home()
    elif page == "Subject Dashboard":
        render_subject_dashboard(subject, config, user_id)
    elif page == "Subject Chatbot":
        render_chat(subject, language, config, user_id)
    elif page == "Quiz Mode":
        render_focused_quiz_mode(user_id, subject, language, config)
    elif page == "Exam Mode":
        render_focused_exam_mode(user_id, subject, language, config)
    elif page == "Learning Goals":
        render_learning_goals(subject)
    elif page == "Study Plan":
        render_study_plan(subject, language)
    elif page == "Exam Grader":
        render_grader(subject, language, config)
    elif page == "Notes Ingestion":
        render_ingestion(subject, config)
    elif page == "Feedback":
        render_feedback(subject)
    elif page == "Help":
        render_help_page(config)
    else:
        render_stats(subject, config)


if __name__ == "__main__":
    main()
