"""Framework-neutral material discovery, upload, syllabus, and indexing services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..config import AppConfig
from ..document_loaders import iter_material_files
from ..material_manifest import load_manifest, stable_material_id
from ..material_router import discover_learning_material, group_material_by_subject
from ..retrieval import build_subject_index
from ..subject_registry import Subject, corpus_keys_for_request, corpus_subjects, get_subject
from ..syllabus_fetcher import ensure_subject_syllabus_cached
from ..user_data_paths import get_user_subject_root


@dataclass(frozen=True)
class MaterialImportResult:
    """Result of storing one uploaded material file."""

    path: Path
    file_name: str
    size_bytes: int


@dataclass(frozen=True)
class MaterialInventoryItem:
    """Framework-neutral metadata for one indexable backend file."""

    material_id: str
    subject_id: str
    component_subject_id: str | None
    material_name: str
    file_name: str
    media_type: str
    section: str | None
    archived: bool
    status: str
    size_bytes: int
    chunks_indexed: int
    created_at: datetime
    indexed_at: datetime | None
    warning: str | None
    source_layer: str


def save_uploaded_material(file_bytes: bytes, original_name: str, subject: Subject) -> MaterialImportResult:
    """Store an uploaded file in the current subject notes directory."""
    safe_name = Path(original_name).name
    if not safe_name:
        raise ValueError("original_name must contain a file name")
    subject.notes_dir.mkdir(parents=True, exist_ok=True)
    target = subject.notes_dir / safe_name
    target.write_bytes(file_bytes)
    return MaterialImportResult(target, safe_name, len(file_bytes))


def discover_material(config: AppConfig) -> dict[str, list[Path]]:
    """Discover external material grouped by current executable subject."""
    paths = discover_learning_material(config)
    return group_material_by_subject(paths, corpus_subjects(config))


def fetch_subject_syllabus(subject: Subject, config: AppConfig):
    """Fetch or read cached official syllabus documents for a subject."""
    return ensure_subject_syllabus_cached(subject, config)


def rebuild_subject_index(subject: Subject, config: AppConfig, *, vector_store=None) -> int:
    """Rebuild a subject index using the existing retrieval implementation."""
    return build_subject_index(subject, config, vector_store=vector_store)


def _material_type(path: Path) -> str:
    """Map supported extensions to frontend material type values."""
    suffix = path.suffix.lower().lstrip(".")
    return "jpeg" if suffix in {"jpg", "jpeg"} else suffix


def _manifest_rows(root: Path) -> list[dict]:
    """Read a manifest when present without implying that one must exist."""
    for name in ("material_manifest.jsonl", "manifest.jsonl"):
        path = root / name
        if path.exists():
            return load_manifest(path)
    return []


def _inventory_item(
    path: Path,
    *,
    root: Path,
    public_subject_id: str,
    corpus_key: str,
    component_subject_id: str | None,
    source_layer: str,
) -> MaterialInventoryItem:
    """Create truthful file metadata using a manifest only when one exists."""
    resolved = str(path.resolve())
    manifest = next(
        (
            row
            for row in _manifest_rows(root)
            if row.get("source_path") == resolved or row.get("source_name") == path.name
        ),
        None,
    )
    stat = path.stat()
    relative = path.relative_to(root)
    section = relative.parts[0] if len(relative.parts) > 1 else None
    archived = any(part.lower() == "archived" for part in relative.parts)
    indexed_at = None
    if manifest and manifest.get("indexed_at"):
        try:
            indexed_at = datetime.fromisoformat(str(manifest["indexed_at"]).replace("Z", "+00:00"))
        except ValueError:
            indexed_at = None
    status = str(manifest.get("status", "uploaded")) if manifest else "uploaded"
    if status not in {"uploaded", "indexing", "indexed", "failed", "needs_review"}:
        status = "uploaded"
    original_name = str(manifest.get("original_name", "")) if manifest else ""
    manifest_material_id = str(manifest.get("material_id", "")) if manifest else ""
    manifest_section = str(manifest.get("section", "")) if manifest else ""
    return MaterialInventoryItem(
        material_id=manifest_material_id or stable_material_id(source_layer, corpus_key, path),
        subject_id=public_subject_id,
        component_subject_id=component_subject_id,
        material_name=Path(original_name).stem if original_name else path.stem,
        file_name=original_name or path.name,
        media_type=_material_type(path),
        section=manifest_section or section,
        archived=archived,
        status=status,
        size_bytes=stat.st_size,
        chunks_indexed=int(manifest.get("chunk_count", 0)) if manifest else 0,
        created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        indexed_at=indexed_at,
        warning=str(manifest.get("notes")) if manifest and manifest.get("notes") else None,
        source_layer=source_layer,
    )


def material_inventory(
    config: AppConfig,
    subject_id: str,
    *,
    component_subject_id: str | None = None,
    student_id: str | None = None,
    section: str | None = None,
    include_archived: bool = False,
) -> list[MaterialInventoryItem]:
    """List canonical files and, when identified, only that student's files."""
    corpus_keys = corpus_keys_for_request(subject_id, component_subject_id)
    items: list[MaterialInventoryItem] = []
    for corpus_key in corpus_keys:
        subject = get_subject(corpus_key, config)
        component = corpus_key if subject_id == "spf_biology_chemistry" else None
        canonical_root = subject.notes_dir.parent
        canonical_paths = iter_material_files(
            [
                subject.syllabus_dir,
                subject.criteria_dir,
                subject.learning_goals_file,
                subject.exam_criteria_file,
            ]
        )
        items.extend(
            _inventory_item(
                path,
                root=canonical_root,
                public_subject_id=subject_id,
                corpus_key=corpus_key,
                component_subject_id=component,
                source_layer="canonical",
            )
            for path in canonical_paths
        )
        if student_id:
            user_root = get_user_subject_root(student_id, corpus_key, config)
            user_paths = iter_material_files(
                [
                    user_root / "notes",
                    user_root / "syllabus",
                    user_root / "criteria",
                    user_root / "learning_goals.md",
                    user_root / "exam_criteria.md",
                ]
            )
            items.extend(
                _inventory_item(
                    path,
                    root=user_root,
                    public_subject_id=subject_id,
                    corpus_key=corpus_key,
                    component_subject_id=component,
                    source_layer="user_material",
                )
                for path in user_paths
            )
    if section:
        items = [item for item in items if (item.section or "").lower() == section.lower()]
    if not include_archived:
        items = [item for item in items if not item.archived]
    return sorted(items, key=lambda item: (item.component_subject_id or "", item.file_name.lower()))
