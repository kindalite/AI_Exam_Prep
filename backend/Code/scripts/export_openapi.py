"""Export the real FastAPI OpenAPI document deterministically."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.api.main import create_app


def main() -> int:
    target = PROJECT_ROOT / "docs" / "openapi.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(create_app().openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"PASS: exported {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
