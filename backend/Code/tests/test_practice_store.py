"""Tests for generated practice and hidden solution storage."""

from __future__ import annotations

from src.practice_store import new_generated_practice, new_performance_report, new_solution_set, practice_records_to_documents, save_generated_exam, save_generated_quiz, save_performance_report, save_solution_set, save_submitted_answers


def test_practice_solution_answers_and_reports_are_saved(temp_config) -> None:
    solution = save_solution_set(new_solution_set(user_id="u", subject_key="german", practice_id="p1", solution_set="secret"), temp_config)
    assert solution["visibility"] == "hidden_until_finished"
    quiz = new_generated_practice(user_id="u", subject_key="german", practice_id="p1", mode="quiz", question_set="Q", solution_set_path=solution["path"])
    save_generated_quiz(quiz, temp_config)
    save_generated_exam(new_generated_practice(user_id="u", subject_key="german", mode="exam", question_set="E", solution_set_path=solution["path"]), temp_config)
    save_submitted_answers("u", "p1", "german", "quiz", "answer", temp_config)
    save_performance_report(new_performance_report(user_id="u", subject_key="german", practice_id="p1", grade=4.5), temp_config)
    docs = practice_records_to_documents("u", temp_config, "german")
    assert any(doc.metadata["source_layer"] == "generated_quiz" for doc in docs)
    assert any(doc.metadata["source_layer"] == "performance_report" for doc in docs)
