"""Readable text chunking helpers for retrieval-augmented generation."""

from __future__ import annotations

from dataclasses import dataclass

from .document_loaders import LoadedDocument


@dataclass(frozen=True)
class TextChunk:
    """A short chunk of source text plus metadata for retrieval."""

    text: str
    metadata: dict[str, str | int]


def chunk_text(text: str, metadata: dict[str, str | int], chunk_size: int = 900, overlap: int = 150) -> list[TextChunk]:
    """Split text into overlapping chunks while preserving metadata."""
    clean_text = text.strip()
    if not clean_text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be zero or smaller than chunk_size")

    chunks: list[TextChunk] = []
    start = 0
    chunk_number = 1
    while start < len(clean_text):
        end = min(start + chunk_size, len(clean_text))
        chunk_metadata = dict(metadata)
        chunk_metadata["chunk_id"] = f"{metadata.get('source_name', 'source')}-{chunk_number}"
        chunk_metadata["chunk_number"] = chunk_number
        chunks.append(TextChunk(text=clean_text[start:end], metadata=chunk_metadata))
        if end == len(clean_text):
            break
        # Move forward but keep a little overlap so ideas split across a boundary are still findable.
        start = end - overlap
        chunk_number += 1
    return chunks


def chunk_documents(documents: list[LoadedDocument], chunk_size: int = 900, overlap: int = 150) -> list[TextChunk]:
    """Chunk every loaded document into retrieval-sized pieces."""
    chunks: list[TextChunk] = []
    for document in documents:
        chunks.extend(chunk_text(document.text, document.metadata, chunk_size=chunk_size, overlap=overlap))
    return chunks

