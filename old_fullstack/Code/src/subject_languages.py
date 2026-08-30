"""Automatic answer-language rules for school subjects."""

from __future__ import annotations


GERMAN_SUBJECTS = {
    "spf_chemistry",
    "spf_biology",
    "german",
    "philosophy",
    "political_education",
    "pedagogics_psychology",
    "chemistry",
    "biology",
}
ENGLISH_SUBJECTS = {"english", "history", "mathematics", "physics"}
FRENCH_SUBJECTS = {"french"}


def language_for_subject(subject_key: str, fallback: str = "German") -> str:
    """Return the required answer language for a subject key."""
    key = subject_key.lower()
    if key in FRENCH_SUBJECTS:
        return "French"
    if key in ENGLISH_SUBJECTS:
        return "English"
    if key in GERMAN_SUBJECTS:
        return "German"
    return fallback


def language_instruction(language: str) -> str:
    """Return extra language guidance for prompts."""
    if language == "French":
        return "Use simple French around CEFR B1. Keep technical words, but explain them simply."
    return f"Answer in {language}."
