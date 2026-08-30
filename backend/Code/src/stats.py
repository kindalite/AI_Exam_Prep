"""Simple local stats and planner helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .adaptive_learning import choose_adaptive_difficulty, recommend_study_actions, suggest_focus_topics
from .grader import calculate_grade
from .performance_tracker import read_practice_attempts, summarize_performance


@dataclass(frozen=True)
class UpcomingExam:
    """Small data holder for an upcoming exam."""

    subject: str
    date: str
    notes: str


def average_grade(grades: list[float]) -> float | None:
    """Return the average grade or None when no grades exist."""
    if not grades:
        return None
    return round(sum(grades) / len(grades), 2)


def grade_table(rows: list[dict]) -> pd.DataFrame:
    """Create a pandas table for grade records."""
    return pd.DataFrame(rows, columns=["subject", "points", "maximum_points", "grade", "date"])


def desired_grade_points(desired_grade: float, maximum_points: float) -> float:
    """Calculate the points needed for a desired Swiss grade."""
    if desired_grade < 1 or desired_grade > 6:
        raise ValueError("desired_grade must be between 1 and 6")
    if maximum_points <= 0:
        raise ValueError("maximum_points must be positive")
    return round(((desired_grade - 1) / 5) * maximum_points, 2)


def practice_grade_row(subject: str, points: float, maximum_points: float, date: str) -> dict:
    """Build one grade table row from points and maximum points."""
    result = calculate_grade(points, maximum_points)
    return {"subject": subject, "points": result.points_achieved, "maximum_points": result.maximum_points, "grade": result.grade, "date": date}


def recent_attempts_table(config, subject_key: str | None = None) -> pd.DataFrame:
    """Return recent local practice attempts as a table."""
    rows = read_practice_attempts(config, subject_key)[-20:]
    return pd.DataFrame(rows)


def subject_performance_summary(subject_key: str, config) -> dict:
    """Return app-ready performance summary values for one subject."""
    return {
        "summary": summarize_performance(subject_key, config),
        "weak_topics": suggest_focus_topics(subject_key, config),
        "next_difficulty": choose_adaptive_difficulty(subject_key, "", config),
        "recommended_actions": recommend_study_actions(subject_key, config),
    }
