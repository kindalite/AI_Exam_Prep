"""Safe streamed upload, parsing, manifest, and user-scoped indexing service."""

from __future__ import annotations

import hashlib
import re
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from shutil import move
from typing import BinaryIO, Callable, Iterator

from ..chunking import chunk_documents
from ..config import AppConfig
from ..document_loaders import SUPPORTED_EXTENSIONS, LoadedDocument, load_document
from ..material_manifest import build_record, save_manifest_record
from ..retrieval import build_user_subject_index
from ..subject_languages import language_for_api_subject
from ..subject_registry import get_subject, validate_component_for_subject, validate_top_level_subject_id
from ..user_data_paths import ensure_user_subject_structure, get_user_subject_root
from .identity_service import StudentContext


ALLOWED_MIME_TYPES: dict[str, set[str]] = {
    ".pdf": {"application/pdf", "application/octet-stream"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/octet-stream"},
    ".md": {"text/markdown", "text/plain", "application/octet-stream"},
    ".txt": {"text/plain", "application/octet-stream"},
    ".png": {"image/png", "application/octet-stream"},
    ".jpg": {"image/jpeg", "application/octet-stream"},
    ".jpeg": {"image/jpeg", "application/octet-stream"},
    ".svg": {"image/svg+xml", "text/xml", "application/xml", "application/octet-stream"},
}


class UploadServiceError(Exception):
    """Base class for upload errors mapped by the HTTP adapter."""


class FileTooLargeError(UploadServiceError):
    """Upload crossed the configured streaming limit."""


class UnsupportedMediaTypeError(UploadServiceError):
    """Filename extension or MIME type is not safely supported."""


class DocumentParseError(UploadServiceError):
    """Document could not be parsed into indexable content."""


class IndexBusyError(UploadServiceError):
    """The same user/corpus collection is already being rebuilt."""


class IndexingFailedError(UploadServiceError):
    """The user-scoped collection rebuild failed."""


@dataclass(frozen=True)
class DocumentImportResult:
    """Framework-neutral result for one accepted upload."""

    material_id: str
    name: str
    media_type: str
    section: str
    language: str
    pages: int | None
    chunks_indexed: int
    status: str
    warnings: tuple[str, ...]
    added_at: datetime


class IndexLockRegistry:
    """Non-blocking per-user/corpus locks for destructive full rebuilds."""

    def __init__(self) -> None:
        self._guard = threading.Lock()
        self._locks: dict[str, threading.Lock] = {}

    @contextmanager
    def hold(self, key: str) -> Iterator[None]:
        """Hold a collection lock or raise immediately when already busy."""
        with self._guard:
            lock = self._locks.setdefault(key, threading.Lock())
        if not lock.acquire(blocking=False):
            raise IndexBusyError(f"Index rebuild already running for {key}")
        try:
            yield
        finally:
            lock.release()


DEFAULT_INDEX_LOCKS = IndexLockRegistry()


def _safe_file_name(original_name: str) -> str:
    """Return a filesystem-safe basename while preserving the display name elsewhere."""
    base = Path(original_name).name
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
    return stem or "material"


def _validate_upload_contract(
    original_name: str,
    content_type: str | None,
    subject_id: str,
    component_subject_id: str | None,
    language: str,
) -> tuple[str, str, str]:
    """Validate media and subject/language fields before writing user storage."""
    normalized_subject = validate_top_level_subject_id(subject_id)
    component = validate_component_for_subject(normalized_subject, component_subject_id)
    if normalized_subject == "spf_biology_chemistry" and component is None:
        raise ValueError("component_subject_id is required for private SPF uploads")
    corpus_key = component or normalized_subject
    expected_language = language_for_api_subject(normalized_subject)
    if language != expected_language:
        raise ValueError(f"language must be {expected_language!r} for {normalized_subject!r}")
    suffix = Path(original_name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS or suffix not in ALLOWED_MIME_TYPES:
        raise UnsupportedMediaTypeError(f"Unsupported file extension: {suffix or 'none'}")
    normalized_mime = (content_type or "application/octet-stream").split(";", 1)[0].strip().lower()
    if normalized_mime not in ALLOWED_MIME_TYPES[suffix]:
        raise UnsupportedMediaTypeError(
            f"MIME type {normalized_mime!r} does not match extension {suffix!r}"
        )
    return normalized_subject, corpus_key, suffix


def _stream_to_temp(stream: BinaryIO, suffix: str, max_bytes: int) -> tuple[Path, str, int]:
    """Copy bounded chunks to a temporary file while hashing content."""
    digest = hashlib.sha256()
    size = 0
    handle = tempfile.NamedTemporaryFile(prefix="alim_upload_", suffix=suffix, delete=False)
    path = Path(handle.name)
    try:
        with handle:
            while True:
                block = stream.read(1024 * 1024)
                if not block:
                    break
                size += len(block)
                if size > max_bytes:
                    raise FileTooLargeError(f"Upload exceeds {max_bytes} bytes")
                digest.update(block)
                handle.write(block)
        return path, digest.hexdigest(), size
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _warnings_from_documents(documents: list[LoadedDocument]) -> list[str]:
    """Collect optional-tool warnings preserved by existing loaders."""
    warnings: list[str] = []
    for document in documents:
        for key, value in document.metadata.items():
            if key.endswith("_warning") and value:
                warnings.append(str(value))
    return list(dict.fromkeys(warnings))


def import_student_document(
    *,
    stream: BinaryIO,
    original_name: str,
    content_type: str | None,
    subject_id: str,
    component_subject_id: str | None,
    section: str,
    language: str,
    student: StudentContext,
    config: AppConfig,
    vector_store=None,
    loader: Callable[..., list[LoadedDocument]] = load_document,
    indexer: Callable[..., int] = build_user_subject_index,
    locks: IndexLockRegistry = DEFAULT_INDEX_LOCKS,
) -> DocumentImportResult:
    """Stream, store, parse, and fully rebuild one isolated user corpus."""
    normalized_subject, corpus_key, suffix = _validate_upload_contract(
        original_name, content_type, subject_id, component_subject_id, language
    )
    if not section.strip():
        raise ValueError("section is required")
    temp_path, content_hash, _size = _stream_to_temp(stream, suffix, config.max_upload_bytes)
    material_id = "mat_" + hashlib.sha256(
        f"{student.student_id}|{corpus_key}|{content_hash}".encode("utf-8")
    ).hexdigest()[:20]
    subject_root = ensure_user_subject_structure(student.student_id, corpus_key, config)
    stored_name = f"{material_id}__{_safe_file_name(original_name)}"
    target = subject_root / "notes" / stored_name
    manifest_path = subject_root / "material_manifest.jsonl"
    added_at = datetime.now(timezone.utc)
    try:
        move(str(temp_path), str(target))
        try:
            documents = loader(target, corpus_key, config=config)
            if not documents or not any(document.text.strip() for document in documents):
                raise ValueError("No indexable text was extracted")
        except Exception as exc:
            save_manifest_record(
                build_record(
                    target,
                    corpus_key,
                    status="needs_review",
                    notes=f"Parse failed: {exc.__class__.__name__}",
                    material_id=material_id,
                    original_name=original_name,
                    section=section,
                    language=language,
                ),
                manifest_path,
            )
            raise DocumentParseError("The document could not be parsed and needs review") from exc

        warnings = _warnings_from_documents(documents)
        chunks = chunk_documents(documents, config.chunk_size, config.chunk_overlap)
        if not chunks:
            save_manifest_record(
                build_record(
                    target,
                    corpus_key,
                    status="needs_review",
                    notes="Parse produced no indexable chunks",
                    material_id=material_id,
                    original_name=original_name,
                    section=section,
                    language=language,
                ),
                manifest_path,
            )
            raise DocumentParseError("The document produced no indexable chunks")
        page_numbers = {
            int(document.metadata["page_number"])
            for document in documents
            if document.metadata.get("page_number") not in {None, ""}
        }
        pages = len(page_numbers) if page_numbers else None
        lock_key = f"{student.student_id}:{corpus_key}"
        with locks.hold(lock_key):
            save_manifest_record(
                build_record(
                    target,
                    corpus_key,
                    status="indexing",
                    material_id=material_id,
                    original_name=original_name,
                    section=section,
                    language=language,
                    chunk_count=len(chunks),
                ),
                manifest_path,
            )
            try:
                indexer(
                    student.student_id,
                    get_subject(corpus_key, config),
                    config,
                    vector_store=vector_store,
                )
            except Exception as exc:
                save_manifest_record(
                    build_record(
                        target,
                        corpus_key,
                        status="needs_review",
                        notes=f"Index failed: {exc.__class__.__name__}",
                        material_id=material_id,
                        original_name=original_name,
                        section=section,
                        language=language,
                        chunk_count=len(chunks),
                    ),
                    manifest_path,
                )
                raise IndexingFailedError("The user-scoped index rebuild failed") from exc
            save_manifest_record(
                build_record(
                    target,
                    corpus_key,
                    status="indexed",
                    notes="; ".join(warnings),
                    material_id=material_id,
                    original_name=original_name,
                    section=section,
                    language=language,
                    chunk_count=len(chunks),
                ),
                manifest_path,
            )
        return DocumentImportResult(
            material_id=material_id,
            name=original_name,
            media_type="jpeg" if suffix in {".jpg", ".jpeg"} else suffix.lstrip("."),
            section=section,
            language=language,
            pages=pages,
            chunks_indexed=len(chunks),
            status="indexed",
            warnings=tuple(warnings),
            added_at=added_at,
        )
    finally:
        temp_path.unlink(missing_ok=True)
