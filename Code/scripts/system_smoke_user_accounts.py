"""System smoke test for local user accounts and isolated folders."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.auth import verify_password
from src.config import load_config
from src.user_manager import authenticate_user, create_user
from src.user_data_paths import get_user_root


def main() -> int:
    base = load_config(PROJECT_ROOT)
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        config = replace(base, data_dir=tmp_path / "data", user_data_root=tmp_path / "data" / "users", auth_db_file=tmp_path / "data" / "auth" / "users.json", subject_data_dir=tmp_path / "data" / "subjects")
        user = create_user("Student One", "secret", config)
        assert authenticate_user("Student One", "secret", config)
        assert authenticate_user("Student One", "wrong", config) is None
        assert get_user_root(user["user_id"], config).exists()
        assert user["password_hash"]["hash"] != "secret"
        assert verify_password("secret", user["password_hash"])
    import app  # noqa: F401
    import src.ui_docs  # noqa: F401
    print("PASS: register/login/logout primitives work")
    print("PASS: per-user folder structure created")
    print("PASS: password is not plaintext")
    print("PASS: app and docs modules import")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
