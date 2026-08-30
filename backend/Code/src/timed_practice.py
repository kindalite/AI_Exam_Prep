"""Shared helpers for timed quiz and exam attempts."""

from __future__ import annotations

from pathlib import Path

from .attempt_session import TimedAttemptSession, create_timed_session, mark_session_status, solution_is_visible
from .grader import calculate_grade
from .practice_store import new_generated_practice, new_performance_report, new_solution_set, save_generated_exam, save_generated_quiz, save_performance_report, save_solution_set, save_submitted_answers
from .rag_memory_indexer import index_user_memory_for_subject
from .user_data_paths import get_user_root


def split_questions_and_solutions(generated_text: str) -> tuple[str, str]:
    """Split generated practice into visible questions and hidden solutions."""
    markers = ["## Solutions", "Solutions:", "Answer key:", "Lösungen:"]
    for marker in markers:
        if marker in generated_text:
            questions, solutions = generated_text.split(marker, 1)
            return questions.strip(), (marker + solutions).strip()
    return generated_text.strip(), "Solutions were not separated by the generator. Ask the model to provide a solution key."


def start_practice_attempt(user_id: str, subject_key: str, mode: str, language: str, topic: str, difficulty_requested: str, difficulty_used: str, timer_minutes: int, generated_text: str, config, sources: list[dict] | None = None) -> tuple[TimedAttemptSession, dict, dict]:
    """Save visible questions, hidden solutions, and start a timer session."""
    questions, solutions = split_questions_and_solutions(generated_text)
    root = get_user_root(user_id, config)
    practice_id = Path(root / "generated_practice").name  # placeholder overwritten below
    solution = new_solution_set(user_id=user_id, subject_key=subject_key, mode=mode, solution_set=solutions)
    solution = new_solution_set(user_id=user_id, subject_key=subject_key, mode=mode, practice_id=solution.practice_id or solution.solution_id, solution_set=solutions)
    practice = new_generated_practice(user_id=user_id, subject_key=subject_key, mode=mode, language=language, topic=topic, difficulty_requested=difficulty_requested, difficulty_used=difficulty_used, timer_seconds=timer_minutes * 60, question_set=questions, solution_set_path="", sources=sources or [])
    solution = new_solution_set(user_id=user_id, subject_key=subject_key, mode=mode, practice_id=practice.practice_id, solution_set=solutions)
    solution_row = save_solution_set(solution, config)
    practice = new_generated_practice(**{**practice.__dict__, "solution_set_path": solution_row["path"]})
    practice_row = save_generated_exam(practice, config) if mode == "exam" else save_generated_quiz(practice, config)
    session = create_timed_session(user_id, subject_key, mode, timer_minutes, practice_row["path"], solution_row["path"], config)
    return session, practice_row, solution_row


def submit_and_grade_attempt(session: TimedAttemptSession, answers: str, points_achieved: float, maximum_points: float, strengths: list[str], weaknesses: list[str], recommended_actions: list[str], config) -> dict:
    """Save answers, grade report, reveal solutions, and index report into user memory."""
    answer_row = save_submitted_answers(session.user_id, session.attempt_id, session.subject_key, session.mode, answers, config)
    grade = calculate_grade(points_achieved, maximum_points).grade
    report = new_performance_report(user_id=session.user_id, subject_key=session.subject_key, practice_id=session.attempt_id, points_achieved=points_achieved, maximum_points=maximum_points, grade=grade, strengths=strengths, weaknesses=weaknesses, recommended_actions=recommended_actions, source_layers_used=["generated_quiz" if session.mode == "quiz" else "generated_exam", "student_answer"])
    report_row = save_performance_report(report, config)
    updated = mark_session_status(session, "graded", config, submitted_answers_path=str(answer_row.get("path", "attempts")), grading_report_path="reports/performance_reports.jsonl")
    index_result = index_user_memory_for_subject(session.user_id, session.subject_key, config)
    return {"session": updated, "grade": grade, "report": report_row, "solutions_visible": solution_is_visible(updated, config), "indexed": index_result}
