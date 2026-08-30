"""Local account management and template material copying."""

from __future__ import annotations

import shutil
from pathlib import Path

from .auth import add_user_record, authenticate_from_db, load_auth_db
from .subject_registry import corpus_subjects
from .user_data_paths import ensure_user_data_structure, get_user_root, get_user_subject_root, sanitize_username
from .utils import ensure_directory


PRIVATE_RELATIVES = ["chat_history", "chat_media", "attempts", "reports", "generated_practice", "rag_exports"]


def _copy_tree_contents(source: Path, target: Path) -> None:
    """Copy all files and folders from source into target."""
    if not source.exists():
        return
    ensure_directory(target)
    for item in source.iterdir():
        destination = target / item.name
        if item.is_dir():
            shutil.copytree(item, destination, dirs_exist_ok=True)
        else:
            ensure_directory(destination.parent)
            shutil.copy2(item, destination)


def copy_template_material_to_new_user(new_user_id: str, template_user_id: str | None, config) -> dict:
    """Copy non-personal study setup into a new user's isolated folders."""
    subjects = corpus_subjects(config)
    ensure_user_data_structure(new_user_id, config, list(subjects.keys()))
    copied_from = None
    if template_user_id:
        template_root = get_user_root(template_user_id, config)
        if template_root.exists():
            for subject_key in subjects:
                src = get_user_subject_root(template_user_id, subject_key, config)
                dst = get_user_subject_root(new_user_id, subject_key, config)
                for child in ["notes", "syllabus", "criteria", "learning_goals.md", "exam_criteria.md"]:
                    source = src / child
                    target = dst / child
                    if source.is_dir():
                        _copy_tree_contents(source, target)
                    elif source.exists():
                        ensure_directory(target.parent)
                        shutil.copy2(source, target)
            copied_from = template_user_id
    else:
        shared = Path(getattr(config, "shared_template_root", None) or (config.data_dir / "shared_templates" / "default_student_material"))
        if shared.exists():
            _copy_tree_contents(shared, get_user_root(new_user_id, config) / "subjects")
            copied_from = str(shared)
    return {"user_id": sanitize_username(new_user_id), "copied_from": copied_from}


def create_user(username: str, password: str, config, template_user_id: str | None = None) -> dict:
    """Create a user, isolated folders, and copied baseline study material."""
    if not username.strip() or not password:
        raise ValueError("Username and password are required.")
    users = list_users(config)
    chosen_template = template_user_id or getattr(config, "default_template_user_id", "") or (users[0]["user_id"] if users else None)
    record = add_user_record(username, password, config, chosen_template)
    copy_template_material_to_new_user(record["user_id"], chosen_template, config)
    return record


def authenticate_user(username: str, password: str, config) -> dict | None:
    """Authenticate a local user by username and password."""
    return authenticate_from_db(username, password, config)


def list_users(config) -> list[dict]:
    """List locally registered users."""
    return load_auth_db(config).get("users", [])
