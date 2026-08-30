"""Copy old single-user data into the new per-user storage layout without deleting originals."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.user_manager import create_user, list_users
from src.user_data_paths import get_user_root
from src.utils import ensure_directory


def main() -> int:
    config = load_config(PROJECT_ROOT)
    users = list_users(config)
    if users:
        user_id = users[0]["user_id"]
        print(f"PASS: users already exist; using {user_id}")
    else:
        user = create_user("alim", "change-me-after-migration", config)
        user_id = user["user_id"]
        print("PASS: created default user alim")
    root = get_user_root(user_id, config)
    if config.subject_data_dir.exists():
        target = root / "subjects"
        ensure_directory(target)
        shutil.copytree(config.subject_data_dir, target, dirs_exist_ok=True)
        print("PASS: copied data/subjects into user storage")
    if config.performance_log_file and Path(config.performance_log_file).exists():
        target = root / "attempts" / "grader_attempts.jsonl"
        ensure_directory(target.parent)
        shutil.copy2(config.performance_log_file, target)
        print("PASS: copied existing performance attempts")
    print("WARN: original data was not deleted; rebuild vector indexes from the app when ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
