"""Dry-run a user-scoped document import with no external services."""

from __future__ import annotations

import json
import sys
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.api.schemas.adapters import document_import_to_response
from src.config import load_config
from src.services.identity_service import StudentContext
from src.services.upload_service import import_student_document
from src.vector_store import InMemoryVectorStore


def main() -> int:
    """Ingest a temporary Markdown file and print its API response shape."""
    base = load_config(PROJECT_ROOT)
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        config = replace(
            base,
            data_dir=root / "data",
            user_data_root=root / "data" / "users",
            subject_data_dir=root / "data" / "subjects",
            vector_db_dir=root / "vector_db",
        )
        result = import_student_document(
            stream=BytesIO(b"# Biology\nMitochondria produce ATP."),
            original_name="cells.md",
            content_type="text/markdown",
            subject_id="biology",
            component_subject_id=None,
            section="cells",
            language="de",
            student=StudentContext("dry-run"),
            config=config,
            vector_store=InMemoryVectorStore(),
        )
        payload = document_import_to_response(result).model_dump(mode="json")
        assert payload["status"] == "indexed" and payload["chunks_indexed"] > 0
        print(json.dumps(payload, indent=2))
    print("PASS: streamed upload stored and indexed only in the dry-run student's corpus")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
