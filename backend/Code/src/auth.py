"""Local-only password hashing and authentication helpers."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from .user_data_paths import sanitize_username
from .utils import ensure_directory, utc_timestamp


@dataclass(frozen=True)
class UserRecord:
    """One locally stored user account."""

    user_id: str
    username: str
    created_at: str
    password_hash: dict
    template_source_user_id: str | None
    role: str = "student"


def create_password_hash(password: str) -> dict:
    """Create a salted PBKDF2 password hash record."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return {"algorithm": "pbkdf2_hmac_sha256", "iterations": 200_000, "salt": salt.hex(), "hash": digest.hex()}


def verify_password(password: str, password_record: dict) -> bool:
    """Return True when a password matches a stored hash record."""
    try:
        salt = bytes.fromhex(password_record["salt"])
        expected = bytes.fromhex(password_record["hash"])
        iterations = int(password_record.get("iterations", 200_000))
    except (KeyError, ValueError, TypeError):
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(digest, expected)


def _auth_path(config) -> Path:
    """Return the local JSON auth database path."""
    configured = getattr(config, "auth_db_file", None)
    return Path(configured or (config.data_dir / "auth" / "users.json"))


def load_auth_db(config) -> dict:
    """Load the local auth database."""
    path = _auth_path(config)
    if not path.exists():
        return {"users": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_auth_db(db: dict, config) -> None:
    """Save the local auth database."""
    path = _auth_path(config)
    ensure_directory(path.parent)
    path.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def add_user_record(username: str, password: str, config, template_user_id: str | None = None) -> dict:
    """Create and persist a local user record."""
    db = load_auth_db(config)
    user_id = sanitize_username(username)
    if any(user.get("user_id") == user_id for user in db.get("users", [])):
        raise ValueError(f"User already exists: {username}")
    record = UserRecord(user_id, username.strip(), utc_timestamp(), create_password_hash(password), template_user_id)
    row = asdict(record)
    db.setdefault("users", []).append(row)
    save_auth_db(db, config)
    return row


def authenticate_from_db(username: str, password: str, config) -> dict | None:
    """Authenticate a user against the local auth database."""
    user_id = sanitize_username(username)
    for user in load_auth_db(config).get("users", []):
        if user.get("user_id") == user_id and verify_password(password, user.get("password_hash", {})):
            return user
    return None
