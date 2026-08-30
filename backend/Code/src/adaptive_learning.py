"""Simple adaptive-learning rules from local performance history."""

from __future__ import annotations

from .performance_tracker import summarize_performance, topic_mastery_scores


def choose_adaptive_difficulty(subject_key: str, topic: str, config) -> str:
    """Choose easy, medium, or hard based on local mastery scores."""
    scores = topic_mastery_scores(subject_key, config)
    mastery = scores.get(topic) if topic else None
    if mastery is None and scores:
        mastery = sum(scores.values()) / len(scores)
    if mastery is None or mastery < 0.55:
        return "easy"
    if mastery < 0.75:
        return "medium"
    return "hard"


def suggest_focus_topics(subject_key: str, config, limit: int = 5) -> list[str]:
    """Return the lowest-mastery topics first."""
    scores = topic_mastery_scores(subject_key, config)
    return [topic for topic, _score in sorted(scores.items(), key=lambda item: item[1])[:limit]]


def build_performance_context(subject_key: str, topic: str, config) -> str:
    """Build text context that can be added to prompts."""
    summary = summarize_performance(subject_key, config)
    difficulty = choose_adaptive_difficulty(subject_key, topic, config)
    focus = suggest_focus_topics(subject_key, config)
    return (
        f"Performance records: {summary['attempt_count']}. Average grade: {summary['average_grade']}. "
        f"Recommended adaptive difficulty for '{topic or 'general'}': {difficulty}. "
        f"Focus topics: {', '.join(focus) if focus else 'No weak topics recorded yet'}."
    )


def recommend_study_actions(subject_key: str, config) -> list[str]:
    """Recommend local study actions from weak topics."""
    topics = suggest_focus_topics(subject_key, config)
    if not topics:
        return ["Add one short practice attempt so the app can personalize suggestions."]
    return [f"Review {topic}, then answer two easy retrieval-based questions." for topic in topics]
