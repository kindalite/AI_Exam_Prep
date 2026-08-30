"""Tests for adaptive difficulty rules."""

from __future__ import annotations

from src.adaptive_learning import choose_adaptive_difficulty
from src.performance_tracker import new_attempt, save_practice_attempt


def test_adaptive_learning_easy_medium_hard(temp_config) -> None:
    assert choose_adaptive_difficulty("biology", "DNA", temp_config) == "easy"
    save_practice_attempt(new_attempt(subject_key="biology", topic="DNA", points_achieved=6, maximum_points=10), temp_config)
    assert choose_adaptive_difficulty("biology", "DNA", temp_config) == "medium"
    save_practice_attempt(new_attempt(subject_key="biology", topic="Atoms", points_achieved=9, maximum_points=10), temp_config)
    assert choose_adaptive_difficulty("biology", "Atoms", temp_config) == "hard"
