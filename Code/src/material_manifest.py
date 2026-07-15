"""JSONL manifest helpers for learning-material indexing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .utils import ensure_directory, utc_timestamp


@dataclass(frozen=True)
class MaterialRecord:
    """One tracked learning-material file."""

    file_id: str
    subject_key: str
    source_path: str
    source_name: str
    source_type: str
    sha256: str
    modified_time: float
    page_count: int
    has_text: bool
    has_ocr: bool
    has_images: bool
    indexed_at: str
    status: str
    notes: str


def calculate_file_hash(path: Path) -> str:
    """Calculate a stable SHA-256 hash for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path) -> list[dict]:
    """Load JSONL manifest rows, ignoring malformed empty lines."""
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def save_manifest_record(record: MaterialRecord, manifest_path: Path) -> None:
    """Append or replace a manifest record by source path."""
    ensure_directory(manifest_path.parent)
    rows = [row for row in load_manifest(manifest_path) if row.get("source_path") != record.source_path]
    rows.append(asdict(record))
    manifest_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def should_reindex(path: Path, existing_record: dict | None) -> bool:
    """Return True when a file is new or has changed since indexing."""
    if existing_record is None:
        return True
    if not path.exists():
        return False
    try:
        return existing_record.get("sha256") != calculate_file_hash(path)
    except OSError:
        return True


def build_record(path: Path, subject_key: str, status: str = "indexed", notes: str = "") -> MaterialRecord:
    """Create a basic manifest record for a path."""
    stat = path.stat()
    return MaterialRecord(
        file_id=calculate_file_hash(path)[:16],
        subject_key=subject_key,
        source_path=str(path),
        source_name=path.name,
        source_type=path.suffix.lower().lstrip("."),
        sha256=calculate_file_hash(path),
        modified_time=stat.st_mtime,
        page_count=0,
        has_text=False,
        has_ocr=False,
        has_images=False,
        indexed_at=utc_timestamp(),
        status=status,
        notes=notes,
    )
