"""Non-authoritative, privacy-minimal per-student AI provenance storage."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import AppConfig
from .user_data_paths import get_user_root, sanitize_username
from .utils import ensure_directory


@dataclass(frozen=True)
class AIProvenanceRecord:
    """AI result metadata only; never a chat message or transcript record."""

    student_id: str
    thread_id: str
    python_message_id: str
    source_ids: tuple[str, ...]
    material_ids: tuple[str, ...]
    used_model: str
    provider: str
    retrieval_summary: dict
    subject_id: str
    component_subject_id: str | None
    language: str
    generated_at: str
    frontend_message_id: str | None = None
    store_role: str = "non_authoritative_ai_provenance"


def ai_metadata_path(student_id: str, config: AppConfig) -> Path:
    """Return one student's append-only AI provenance path."""
    return get_user_root(student_id, config) / "ai_metadata" / "results.jsonl"


def save_ai_provenance(record: AIProvenanceRecord, config: AppConfig) -> dict:
    """Append one provenance record without prompt or answer text."""
    safe_student = sanitize_username(record.student_id)
    row = asdict(record) | {"student_id": safe_student}
    path = ai_metadata_path(safe_student, config)
    ensure_directory(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def read_ai_provenance(student_id: str, config: AppConfig) -> list[dict]:
    """Read valid provenance rows while skipping malformed lines."""
    path = ai_metadata_path(student_id, config)
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def find_ai_provenance(
    student_id: str,
    thread_id: str,
    python_message_id: str,
    config: AppConfig,
) -> dict | None:
    """Look up the latest exact student/thread/Python-result key."""
    for row in reversed(read_ai_provenance(student_id, config)):
        if row.get("thread_id") == thread_id and row.get("python_message_id") == python_message_id:
            return row
    return None
