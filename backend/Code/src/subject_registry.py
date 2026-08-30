"""Subject registry with paths, language defaults, and study instructions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig, load_config
from .subject_languages import API_LANGUAGE_NAMES, language_for_api_subject
from .utils import ensure_directory, write_text_if_missing


@dataclass(frozen=True)
class Subject:
    """Configuration for one school subject."""

    key: str
    display_name: str
    default_language: str
    notes_dir: Path
    syllabus_dir: Path
    criteria_dir: Path
    learning_goals_file: Path
    exam_criteria_file: Path
    collection_name: str
    instructions: str
    api_language: str
    is_top_level: bool = True
    is_virtual: bool = False
    components: tuple[str, ...] = ()
    legacy_storage_keys: tuple[str, ...] = ()


TOP_LEVEL_SUBJECT_IDS: tuple[str, ...] = (
    "mathematics",
    "physics",
    "english",
    "history",
    "french",
    "german",
    "biology",
    "chemistry",
    "spf_biology_chemistry",
    "philosophy",
    "political_education",
    "pedagogics_psychology",
    "economics",
    "art",
    "sport",
)

COMPONENT_SUBJECT_IDS: tuple[str, ...] = ("spf_biology", "spf_chemistry")
SPF_PARENT_SUBJECT_ID = "spf_biology_chemistry"

# Legacy keys are retained as explicit, non-destructive read/migration aliases.
LEGACY_STORAGE_ALIASES: dict[str, tuple[str, ...]] = {
    "maths_physics": ("mathematics", "physics"),
    "spf_biology": ("spf_biology",),
    "spf_chemistry": ("spf_chemistry",),
}


SUBJECT_DEFINITIONS: tuple[tuple[str, str, str, bool, tuple[str, ...], tuple[str, ...]], ...] = (
    ("mathematics", "Mathematics", "Generate similar problems, show correct methods, and include final answers.", False, (), ("maths_physics",)),
    ("physics", "Physics", "Explain physical ideas, solve problems step by step, and connect formulas to units and experiments.", False, (), ("maths_physics",)),
    ("english", "English", "Analyze grammar exercises and books, then create class-style questions.", False, (), ()),
    ("history", "History", "Place events and texts in historical context and test all given material.", False, (), ()),
    ("french", "French", "Use simple CEFR B1 French for vocabulary, grammar explanations, and similar exercises.", False, (), ()),
    ("german", "German", "Create vocabulary quizlets, class-style literature questions, and writing feedback.", False, (), ()),
    ("biology", "Biology", "Analyze biology material and answer from pages, PDFs, notes, syllabus, and criteria.", False, (), ()),
    ("chemistry", "Chemistry", "Stay inside class scope and explain concepts, graphics, and simple molecule descriptions.", False, (), ()),
    (SPF_PARENT_SUBJECT_ID, "SPF Biology/Chemistry", "Combine the selected SPF biology and chemistry component corpora without duplicating them.", True, COMPONENT_SUBJECT_IDS, ()),
    ("philosophy", "Philosophy", "Explain arguments clearly and connect ideas to the treated material.", False, (), ()),
    ("political_education", "Political Education", "Analyze political education material and connect answers to course criteria.", False, (), ()),
    ("pedagogics_psychology", "Pedagogics/Psychology", "Use course concepts to analyze examples and answer exam-style questions.", False, (), ()),
    ("economics", "Economics", "Explain economic concepts and apply them to course examples and exam tasks.", False, (), ()),
    ("art", "Art", "Analyze artworks, techniques, visual language, and course material clearly.", False, (), ()),
    ("sport", "Sport", "Explain sports science, training principles, and course concepts clearly.", False, (), ()),
    ("spf_biology", "SPF Biology", "Analyze advanced biology material and answer from pages, PDFs, notes, syllabus, and criteria.", False, (), ()),
    ("spf_chemistry", "SPF Chemistry", "Analyze advanced chemistry exercises, create similar tasks, and describe molecules.", False, (), ()),
)


def build_subject_registry(config: AppConfig | None = None) -> dict[str, Subject]:
    """Create all subject configurations from the current app settings."""
    app_config = config or load_config()
    subjects: dict[str, Subject] = {}
    for key, display_name, instructions, is_virtual, components, legacy_keys in SUBJECT_DEFINITIONS:
        subject_dir = app_config.subject_data_dir / key
        api_language = language_for_api_subject(key)
        subjects[key] = Subject(
            key=key,
            display_name=display_name,
            default_language=API_LANGUAGE_NAMES[api_language],
            notes_dir=subject_dir / "notes",
            syllabus_dir=subject_dir / "syllabus",
            criteria_dir=subject_dir / "criteria",
            learning_goals_file=subject_dir / "learning_goals.md",
            exam_criteria_file=subject_dir / "exam_criteria.md",
            collection_name=f"subject_{key}",
            instructions=instructions,
            api_language=api_language,
            is_top_level=key in TOP_LEVEL_SUBJECT_IDS,
            is_virtual=is_virtual,
            components=components,
            legacy_storage_keys=legacy_keys,
        )
    return subjects


def get_subject(subject_key: str, config: AppConfig | None = None) -> Subject:
    """Return one subject or raise a helpful KeyError if it does not exist."""
    subjects = build_subject_registry(config)
    if subject_key not in subjects:
        raise KeyError(f"Unknown subject key: {subject_key}")
    return subjects[subject_key]


def setup_subject_folders(config: AppConfig | None = None) -> None:
    """Create subject folders and starter files for a new local project."""
    for subject in build_subject_registry(config).values():
        if subject.is_virtual:
            continue
        ensure_directory(subject.notes_dir)
        ensure_directory(subject.syllabus_dir)
        ensure_directory(subject.criteria_dir)
        write_text_if_missing(
            subject.learning_goals_file,
            f"# Learning Goals: {subject.display_name}\n\nAdd exam learning goals here.\n",
        )
        write_text_if_missing(
            subject.exam_criteria_file,
            f"# Exam Criteria: {subject.display_name}\n\nAdd teacher criteria and grading expectations here.\n",
        )


def subjects_for_display(config: AppConfig | None = None) -> list[Subject]:
    """Return the 15 top-level subjects in the frontend's frozen order."""
    subjects = build_subject_registry(config)
    return [subjects[subject_id] for subject_id in TOP_LEVEL_SUBJECT_IDS]


def corpus_subjects(config: AppConfig | None = None) -> dict[str, Subject]:
    """Return concrete corpus subjects, excluding the virtual SPF parent."""
    return {
        key: subject
        for key, subject in build_subject_registry(config).items()
        if not subject.is_virtual
    }


def validate_top_level_subject_id(subject_id: str) -> str:
    """Validate and return a public top-level subject ID."""
    normalized = subject_id.strip().lower()
    if normalized not in TOP_LEVEL_SUBJECT_IDS:
        raise ValueError(f"Invalid top-level subject_id: {subject_id}")
    return normalized


def validate_component_for_subject(subject_id: str, component_subject_id: str | None) -> str | None:
    """Validate the optional SPF component selection for a top-level subject."""
    normalized_subject = validate_top_level_subject_id(subject_id)
    if component_subject_id is None:
        return None
    normalized_component = component_subject_id.strip().lower()
    if normalized_subject != SPF_PARENT_SUBJECT_ID:
        raise ValueError("component_subject_id is only valid for spf_biology_chemistry")
    if normalized_component not in COMPONENT_SUBJECT_IDS:
        raise ValueError(f"Invalid SPF component_subject_id: {component_subject_id}")
    return normalized_component


def corpus_keys_for_request(subject_id: str, component_subject_id: str | None = None) -> tuple[str, ...]:
    """Resolve a public subject/component request to one or more corpus keys."""
    normalized_subject = validate_top_level_subject_id(subject_id)
    normalized_component = validate_component_for_subject(normalized_subject, component_subject_id)
    if normalized_subject == SPF_PARENT_SUBJECT_ID:
        return (normalized_component,) if normalized_component else COMPONENT_SUBJECT_IDS
    return (normalized_subject,)
