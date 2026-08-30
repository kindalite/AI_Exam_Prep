"""Stable API language rules for school subjects."""

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
    "spf_biology_chemistry",
    "economics",
    "art",
    "sport",
}
ENGLISH_SUBJECTS = {"english", "history", "mathematics", "physics"}
FRENCH_SUBJECTS = {"french"}

API_LANGUAGE_NAMES = {"de": "German", "en": "English", "fr": "French"}
LANGUAGE_NAME_TO_API = {value.lower(): key for key, value in API_LANGUAGE_NAMES.items()}


def language_for_api_subject(subject_id: str) -> str:
    """Return the frozen API language code for a subject or component ID."""
    key = subject_id.strip().lower()
    if key in FRENCH_SUBJECTS:
        return "fr"
    if key in ENGLISH_SUBJECTS:
        return "en"
    if key in GERMAN_SUBJECTS:
        return "de"
    raise ValueError(f"Unknown subject ID: {subject_id}")


def language_name(language: str) -> str:
    """Normalize an API code or supported language name to its display name."""
    normalized = language.strip().lower()
    if normalized in API_LANGUAGE_NAMES:
        return API_LANGUAGE_NAMES[normalized]
    if normalized in LANGUAGE_NAME_TO_API:
        return API_LANGUAGE_NAMES[LANGUAGE_NAME_TO_API[normalized]]
    raise ValueError(f"Unsupported language: {language}")


def language_for_subject(subject_key: str, fallback: str = "German") -> str:
    """Return the legacy language name for a subject key."""
    try:
        return API_LANGUAGE_NAMES[language_for_api_subject(subject_key)]
    except ValueError:
        return fallback


def language_instruction(language: str) -> str:
    """Return the precise school-register instruction for an API code or name."""
    normalized = language_name(language)
    if normalized == "French":
        return (
            "Answer in simple CEFR B1 French. Use short sentences and common "
            "vocabulary; add a brief gloss only when a technical term needs it."
        )
    if normalized == "English":
        return "Answer in clear academic English at Swiss Gymnasium Grade-11 level."
    return "Answer in German using an appropriate Swiss Gymnasium Grade-11 register."
