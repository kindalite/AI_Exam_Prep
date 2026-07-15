"""Local OCR helpers that never crash the app when Tesseract is missing."""

from __future__ import annotations

import shutil
from pathlib import Path


def is_tesseract_available() -> bool:
    """Return True when the tesseract executable is installed."""
    return shutil.which("tesseract") is not None


def ocr_image(image_path: Path, languages: str) -> str:
    """Read text from an image with local Tesseract."""
    if not is_tesseract_available():
        raise RuntimeError("Tesseract OCR is not installed.")
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Install pytesseract and pillow to use OCR.") from exc
    return pytesseract.image_to_string(Image.open(image_path), lang=languages)


def ocr_image_safe(image_path: Path, languages: str) -> tuple[str, str | None]:
    """OCR an image and return text plus an optional warning."""
    if not image_path.exists():
        return "", f"Image file was not found: {image_path}"
    try:
        return ocr_image(image_path, languages), None
    except Exception as exc:  # noqa: BLE001 - this is a UI fallback boundary.
        return "", f"OCR unavailable for {image_path.name}: {exc}"
