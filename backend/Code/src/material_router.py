"""Find external learning material and map files to known subjects."""

from __future__ import annotations

from pathlib import Path

from .document_loaders import SUPPORTED_EXTENSIONS
from .subject_registry import Subject

SUBJECT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "spf_biology": ("spf biology", "spf biologie"),
    "spf_chemistry": ("spf chemistry", "spf chemie"),
    "biology": ("biology", "biologie", "bio"),
    "chemistry": ("chemistry", "chemie", "chem"),
    "french": ("franz", "franzoesisch", "französisch", "french"),
    "german": ("deutsch", "german"),
    "english": ("english", "englisch"),
    "history": ("history", "geschichte"),
    "mathematics": ("math", "maths", "mathematik", "mathematics", "mathe"),
    "physics": ("physics", "physik"),
    "philosophy": ("philosophy", "philosophie"),
    "pedagogics_psychology": ("pedagogics", "psychology", "pädagogik", "paedagogik", "psychologie"),
    "political_education": ("politics", "politische bildung", "political education"),
    "economics": ("economics", "economy", "wirtschaft"),
    "art": ("art", "kunst"),
    "sport": ("sport", "physical education", "sportunterricht"),
}

LEGACY_SHARED_FOLDERS: dict[str, tuple[str, ...]] = {
    "maths & physics": ("mathematics", "physics"),
    "maths and physics": ("mathematics", "physics"),
    "maths physics": ("mathematics", "physics"),
}


def discover_learning_material(config) -> list[Path]:
    """Return supported files below the configured external learning-material root."""
    root = getattr(config, "learning_material_root", None)
    if root is None or not Path(root).exists():
        return []
    return sorted(path for path in Path(root).rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS)


def guess_subject_from_path(path: Path, subjects: dict[str, Subject]) -> str | None:
    """Guess the best subject key from folder and file names."""
    text = " ".join(part.lower() for part in path.parts[-4:]).replace("_", " ").replace("-", " ")
    exact_folder = path.parent.name.lower().replace("_", " ").replace("-", " ")
    if exact_folder.startswith("spf "):
        for component_key in ("spf_biology", "spf_chemistry"):
            if component_key in subjects and any(
                keyword == exact_folder for keyword in SUBJECT_KEYWORDS[component_key]
            ):
                return component_key
    if exact_folder in LEGACY_SHARED_FOLDERS:
        return next((key for key in LEGACY_SHARED_FOLDERS[exact_folder] if key in subjects), None)
    for key, subject in subjects.items():
        if subject.is_virtual:
            continue
        display = subject.display_name.lower().replace("/", " ")
        if key.replace("_", " ") == exact_folder or display == exact_folder:
            return key
    for key, keywords in SUBJECT_KEYWORDS.items():
        if key not in subjects:
            continue
        if any(keyword in exact_folder for keyword in keywords):
            return key
    for key, keywords in SUBJECT_KEYWORDS.items():
        if key in subjects and any(keyword in text for keyword in keywords):
            return key
    return None


def group_material_by_subject(paths: list[Path], subjects: dict[str, Subject]) -> dict[str, list[Path]]:
    """Group discovered material paths by guessed subject key."""
    grouped: dict[str, list[Path]] = {key: [] for key in subjects}
    grouped["unassigned"] = []
    for path in paths:
        exact_folder = path.parent.name.lower().replace("_", " ").replace("-", " ")
        shared_keys = LEGACY_SHARED_FOLDERS.get(exact_folder, ())
        if shared_keys:
            for key in shared_keys:
                if key in subjects:
                    grouped[key].append(path)
            continue
        subject_key = guess_subject_from_path(path, subjects)
        grouped[subject_key if subject_key else "unassigned"].append(path)
    return {key: value for key, value in grouped.items() if value}
