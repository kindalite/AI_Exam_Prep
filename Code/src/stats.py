"""Simple local stats and planner placeholder helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .grader import calculate_grade


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
    return {
        "subject": subject,
        "points": result.points_achieved,
        "maximum_points": result.maximum_points,
        "grade": result.grade,
        "date": date,
    }

