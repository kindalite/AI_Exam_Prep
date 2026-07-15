"""Streamlit UI for the local Alim Study Assistant web app."""

from __future__ import annotations

from datetime import date
from pathlib import Path

try:
    import streamlit as st
except ImportError:  # Keeps smoke imports working before Streamlit is installed.
    st = None

from src.audio_transcription import transcribe_audio_safe
from src.config import load_config
from src.chat_history_store import new_chat_message, save_chat_message, save_chat_media
from src.feedback import save_feedback
from src.grader import calculate_grade, create_grading_feedback, store_grading_attempt
from src.image_understanding import describe_image_safe
from src.material_router import discover_learning_material, group_material_by_subject
from src.ocr import ocr_image_safe
from src.performance_tracker import new_attempt, save_practice_attempt
from src.prompts import build_multimodal_chat_prompt, build_system_prompt
from src.llm_client import generate_response
from src.mock_exam_generator import create_mock_exam
from src.quiz_generator import create_quiz
from src.retrieval import build_subject_index, load_exam_criteria, load_learning_goals, retrieve_study_context
from src.stats import average_grade, desired_grade_points, grade_table, practice_grade_row, recent_attempts_table, subject_performance_summary
from src.study_plan_generator import create_study_plan
from src.subject_registry import build_subject_registry, setup_subject_folders, subjects_for_display
from src.syllabus_fetcher import ensure_subject_syllabus_cached
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
    subjects = subjects_for_display(config)
    subject_names = [subject.display_name for subject in subjects]
    selected_name = st.sidebar.selectbox("Subject", subject_names)
    subject = next(item for item in subjects if item.display_name == selected_name)
    languages = ["German", "English", "French"]
    default_index = languages.index(subject.default_language) if subject.default_language in languages else 0
    language = st.sidebar.selectbox("Language", languages, index=default_index)
    st.sidebar.caption(f"Local model: {config.ollama_model}")
    return config, subject, language


def _save_uploaded_file(uploaded_file, folder: Path) -> Path:
    """Persist a Streamlit upload under a local runtime folder."""
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / uploaded_file.name
    target.write_bytes(uploaded_file.getbuffer())
    return target


def render_home() -> None:
    """Render the home page."""
    st.title("Alim Study Assistant")
    st.write("Local exam preparation with retrieval, quizzes, mock exams, planning, grading, multimodal inputs, syllabus fallback, and adaptive practice memory.")
    st.info("Private notes, images, and audio stay local. Public web retrieval is only used when you enable it.")


def render_ingestion(subject, config) -> None:
    """Render material ingestion controls."""
    st.header("Notes and Material Ingestion")
    st.write(f"Subject notes folder: `{subject.notes_dir}`")
    st.write(f"External learning material root: `{config.learning_material_root}`")
    st.write("Root exists." if config.learning_material_root and config.learning_material_root.exists() else "Root not found yet.")

    uploaded_files = st.file_uploader("Add MD, TXT, PDF, DOCX, PNG, or JPG material", accept_multiple_files=True, type=["md", "txt", "pdf", "docx", "png", "jpg", "jpeg"])
    if uploaded_files:
        subject.notes_dir.mkdir(parents=True, exist_ok=True)
        for uploaded_file in uploaded_files:
            _save_uploaded_file(uploaded_file, subject.notes_dir)
        st.success(f"Saved {len(uploaded_files)} file(s).")

    paths = discover_learning_material(config)
    grouped = group_material_by_subject(paths, build_subject_registry(config))
    st.subheader("Discovered external material")
    if grouped:
        for key, files in grouped.items():
            st.caption(f"{key}: {len(files)} file(s)")
            for path in files[:8]:
                st.text(str(path))
    else:
        st.caption("No external supported files discovered yet.")

    if st.button("Fetch/cache official KSA/Lucerne syllabus for this subject"):
        docs = ensure_subject_syllabus_cached(subject, config)
        st.success(f"Cached {len(docs)} syllabus document(s) for {subject.display_name}.")
    if st.button("Build or rebuild subject database"):
        count = build_subject_index(subject, config)
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
        runtime_dir = config.data_dir / "runtime_uploads"
        warnings: list[str] = []
        image_ocr = ""
        image_description = ""
        audio_transcript = ""
        if image_file:
            image_path = save_chat_media(image_file.getbuffer(), image_file.name, user_id, "image", config)
            image_ocr, warning = ocr_image_safe(image_path, config.ocr_languages)
            if warning:
                warnings.append(warning)
            image_description, warning = describe_image_safe(image_path, subject.key, config)
            if warning:
                warnings.append(warning)
            st.text_area("Image OCR", value=image_ocr, height=120)
            st.text_area("Image description", value=image_description, height=120)
        if audio_file:
            audio_path = save_chat_media(audio_file.getbuffer(), audio_file.name, user_id, "audio", config)
            audio_transcript, warning = transcribe_audio_safe(audio_path, config)
            if warning:
                warnings.append(warning)
            st.text_area("Audio transcript", value=audio_transcript, height=120)

        search_query = "\n".join(part for part in [question, audio_transcript, image_ocr, image_description] if part).strip()
        study_context = retrieve_study_context(subject, search_query or subject.display_name, config=config, include_syllabus=use_syllabus, include_web=use_web, include_performance=True)
        prompt = build_multimodal_chat_prompt(
            subject,
            language,
            question,
            study_context.local_context,
            study_context.syllabus_context,
            study_context.web_context,
            study_context.performance_context,
            load_learning_goals(subject),
            load_exam_criteria(subject),
            audio_transcript,
            image_ocr,
            image_description,
            warnings + study_context.warnings,
        )
        response = generate_response(prompt, build_system_prompt(subject, language), config=config)
        if response.ok:
            st.markdown(response.text)
            save_practice_attempt(new_attempt(subject_key=subject.key, topic=question[:80], feature="chat", difficulty="adaptive", question=question, model_feedback=response.text), config)
            save_chat_message(new_chat_message(user_id=user_id, subject_key=subject.key, language=language, user_text=question, audio_transcript=audio_transcript or None, image_ocr=image_ocr or None, image_description=image_description or None, assistant_answer=response.text, source_chunk_ids=[str(source.metadata.get("chunk_id", "")) for source in study_context.sources], source_layers=[str(source.metadata.get("source_layer", "")) for source in study_context.sources], topic=question[:80]), config)
        else:
            st.warning(response.error)
            st.code(prompt)
        if warnings or study_context.warnings:
            st.subheader("Warnings")
            for warning in warnings + study_context.warnings:
                st.warning(warning)
        if study_context.sources:
            st.subheader("Sources")
            for source in study_context.sources:
                layer = source.metadata.get("source_layer", "local_material")
                name = source.metadata.get("source_name", "source")
                page = source.metadata.get("page_number", "")
                modality = source.metadata.get("modality", "")
                url = source.metadata.get("url", "")
                st.caption(f"{layer}: {name} {f'page {page}' if page else ''} {modality} {url}")


def render_learning_goals(subject) -> None:
    """Show learning goals and relevant retrieved material."""
    st.header("Learning Goals")
    goals = load_learning_goals(subject)
    st.text_area("Stored learning goals", value=goals, height=220)
    selected_goal = st.text_input("Paste or select a learning goal to connect with notes")
    if st.button("Find relevant material") and selected_goal:
        context = retrieve_study_context(subject, selected_goal)
        st.text(context.local_context or context.syllabus_context or "No source context found yet.")


def render_quiz(subject, language) -> None:
    """Render quiz generation controls."""
    st.header("Quiz Generator")
    learning_goal = st.text_input("Learning goal or topic")
    difficulty = st.selectbox("Difficulty", ["adaptive", "easy", "medium", "hard"])
    if st.button("Generate quiz"):
        response = create_quiz(subject, language, learning_goal, difficulty)
        st.markdown(response.text if response.ok else response.error)


def render_mock_exam(subject, language) -> None:
    """Render mock exam generation controls."""
    st.header("Mock Exam Generator")
    total_points = st.number_input("Total points", min_value=1, value=50)
    difficulty = st.selectbox("Exam difficulty", ["adaptive", "easy", "medium", "hard"])
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


def render_grader(subject, language, config) -> None:
    """Render the practice grader."""
    st.header("Practice Exam Grader")
    question = st.text_area("Question")
    answer = st.text_area("Student answer")
    max_points = st.number_input("Maximum points", min_value=1.0, value=10.0)
    achieved = st.number_input("Manual points achieved for formula check", min_value=0.0, max_value=float(max_points), value=0.0)
    result = calculate_grade(float(achieved), float(max_points))
    st.write(f"Formula grade: {result.grade}")
    marking_scheme = st.text_area("Optional marking scheme")
    if st.button("Ask AI for practice feedback"):
        response = create_grading_feedback(subject, language, question, answer, float(max_points), marking_scheme)
        st.markdown(response.text if response.ok else response.error)
    if st.button("Save this manual grade to performance memory"):
        store_grading_attempt(subject, question, answer, "Manual grade saved from grader page.", float(achieved), float(max_points), config)
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
        save_feedback(subject.key, feature, task, answer, rating, comment)
        st.success("Feedback saved locally.")


def render_stats(subject, config) -> None:
    """Render performance stats and planner placeholders."""
    st.header("Stats and Planner")
    summary = subject_performance_summary(subject.key, config)
    st.write(f"Next recommended difficulty: {summary['next_difficulty']}")
    st.write("Recommended actions:")
    for action in summary["recommended_actions"]:
        st.caption(action)
    table = recent_attempts_table(config, subject.key)
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
    st.set_page_config(page_title="Alim Study Assistant", layout="wide")
    st.markdown("<style>:root{--primary-color:#2563eb;} .stButton button{border-radius:6px;} section[data-testid=stSidebar]{background:#eff6ff;}</style>", unsafe_allow_html=True)
    user = require_login(config)
    if user is None:
        return
    user_id = user["user_id"]
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
