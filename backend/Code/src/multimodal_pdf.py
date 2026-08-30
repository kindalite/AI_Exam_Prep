"""Multimodal PDF loading for OneNote-exported study pages."""

from __future__ import annotations

from pathlib import Path

from .document_loaders import LoadedDocument
from .image_understanding import describe_image_safe
from .ocr import ocr_image_safe
from .utils import ensure_directory, utc_timestamp


def _base_metadata(pdf_path: Path, subject_key: str, page_number: int | None = None) -> dict[str, str | int]:
    """Build shared metadata for PDF-derived documents."""
    metadata: dict[str, str | int] = {
        "subject": subject_key,
        "source_path": str(pdf_path),
        "source_name": pdf_path.name,
        "source_type": "pdf",
        "source_layer": "local_material",
        "loaded_at": utc_timestamp(),
    }
    if page_number is not None:
        metadata["page_number"] = page_number
    return metadata


def render_pdf_page_to_image(pdf_path: Path, page_index: int, output_dir: Path, dpi: int) -> Path:
    """Render one PDF page to a PNG image with PyMuPDF."""
    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("pymupdf is required for PDF page rendering.") from exc
    ensure_directory(output_dir)
    document = fitz.open(str(pdf_path))
    page = document.load_page(page_index)
    zoom = dpi / 72
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    output_path = output_dir / f"{pdf_path.stem}_page_{page_index + 1}.png"
    pixmap.save(str(output_path))
    document.close()
    return output_path


def extract_embedded_images(pdf_path: Path, output_dir: Path) -> list[Path]:
    """Extract embedded images from a PDF when PyMuPDF is installed."""
    try:
        import fitz
    except ImportError:
        return []
    ensure_directory(output_dir)
    images: list[Path] = []
    document = fitz.open(str(pdf_path))
    for page_index in range(len(document)):
        for image_index, image in enumerate(document[page_index].get_images(full=True), start=1):
            xref = image[0]
            extracted = document.extract_image(xref)
            extension = extracted.get("ext", "png")
            output_path = output_dir / f"{pdf_path.stem}_page_{page_index + 1}_image_{image_index}.{extension}"
            output_path.write_bytes(extracted["image"])
            images.append(output_path)
    document.close()
    return images


def _load_selectable_text(pdf_path: Path, subject_key: str) -> list[LoadedDocument]:
    """Extract selectable PDF text with pypdf as a safe baseline."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return []
    try:
        reader = PdfReader(str(pdf_path))
    except Exception:
        return []
    documents: list[LoadedDocument] = []
    for page_index, page in enumerate(reader.pages, start=1):
        metadata = _base_metadata(pdf_path, subject_key, page_index)
        metadata["modality"] = "pdf_text"
        documents.append(LoadedDocument(text=page.extract_text() or "", metadata=metadata))
    return documents


def _page_count(pdf_path: Path, fallback_count: int) -> int:
    """Return PDF page count through PyMuPDF when available."""
    try:
        import fitz

        document = fitz.open(str(pdf_path))
        count = len(document)
        document.close()
        return count
    except Exception:
        return fallback_count


def load_pdf_multimodal(pdf_path: Path, subject_key: str, config) -> list[LoadedDocument]:
    """Load selectable text, OCR text, and local vision descriptions from a PDF."""
    documents = _load_selectable_text(pdf_path, subject_key)
    page_total = _page_count(pdf_path, len(documents))
    image_dir = Path(getattr(config, "data_dir", pdf_path.parent)) / "rendered_pages" / subject_key

    if getattr(config, "enable_pdf_page_rendering", True):
        for page_index in range(page_total):
            try:
                image_path = render_pdf_page_to_image(pdf_path, page_index, image_dir, getattr(config, "pdf_render_dpi", 200))
            except Exception as exc:
                metadata = _base_metadata(pdf_path, subject_key, page_index + 1)
                metadata["modality"] = "page_image_description"
                metadata["vision_warning"] = f"PDF page rendering unavailable: {exc}"
                documents.append(LoadedDocument(text="", metadata=metadata))
                continue
            if getattr(config, "enable_ocr", True):
                text, warning = ocr_image_safe(image_path, getattr(config, "ocr_languages", "deu+eng+fra"))
                metadata = _base_metadata(pdf_path, subject_key, page_index + 1)
                metadata.update({"modality": "ocr_text", "image_path": str(image_path)})
                if warning:
                    metadata["ocr_warning"] = warning
                documents.append(LoadedDocument(text=text, metadata=metadata))
            if getattr(config, "enable_image_understanding", True):
                description, warning = describe_image_safe(image_path, subject_key, config)
                metadata = _base_metadata(pdf_path, subject_key, page_index + 1)
                metadata.update({"modality": "page_image_description", "image_path": str(image_path)})
                if warning:
                    metadata["vision_warning"] = warning
                documents.append(LoadedDocument(text=description, metadata=metadata))

    embedded_dir = Path(getattr(config, "data_dir", pdf_path.parent)) / "embedded_images" / subject_key
    for image_index, image_path in enumerate(extract_embedded_images(pdf_path, embedded_dir), start=1):
        description, warning = describe_image_safe(image_path, subject_key, config)
        metadata = _base_metadata(pdf_path, subject_key)
        metadata.update({"modality": "embedded_image_description", "image_path": str(image_path), "image_index": image_index})
        if warning:
            metadata["vision_warning"] = warning
        documents.append(LoadedDocument(text=description, metadata=metadata))
    return documents
