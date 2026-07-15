"""Local vector store helpers with Chroma support and a JSON-free test fallback."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from .chunking import TextChunk
from .embeddings import HashEmbeddingFunction, get_embedding_function
from .utils import ensure_directory


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned from vector retrieval."""

    text: str
    metadata: dict[str, str | int | float]
    score: float


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for two vectors."""
    numerator = sum(a * b for a, b in zip(left, right))
    left_length = math.sqrt(sum(a * a for a in left)) or 1.0
    right_length = math.sqrt(sum(b * b for b in right)) or 1.0
    return numerator / (left_length * right_length)


def _matches_where(metadata: dict, where: dict | None) -> bool:
    """Return True when metadata contains every requested filter value."""
    if not where:
        return True
    return all(metadata.get(key) == value for key, value in where.items())


class InMemoryVectorStore:
    """Tiny vector store used by tests and dry-run scripts."""

    def __init__(self, embedding_function: HashEmbeddingFunction | None = None) -> None:
        """Create an empty in-memory vector store."""
        self.embedding_function = embedding_function or HashEmbeddingFunction()
        self._collections: dict[str, list[tuple[str, TextChunk, list[float]]]] = {}

    def rebuild_collection(self, collection_name: str, chunks: list[TextChunk]) -> int:
        """Replace a collection with new chunks and return how many were stored."""
        stored_chunks: list[tuple[str, TextChunk, list[float]]] = []
        for index, chunk in enumerate(chunks):
            chunk_id = str(chunk.metadata.get("chunk_id", f"{collection_name}-{index}"))
            stored_chunks.append((chunk_id, chunk, self.embedding_function.embed_text(chunk.text)))
        self._collections[collection_name] = stored_chunks
        return len(stored_chunks)

    def query(self, collection_name: str, question: str, top_k: int = 4, where: dict | None = None) -> list[RetrievedChunk]:
        """Return the most similar chunks for a query from one collection."""
        if collection_name not in self._collections:
            return []
        query_vector = self.embedding_function.embed_text(question)
        scored: list[RetrievedChunk] = []
        for _chunk_id, chunk, vector in self._collections[collection_name]:
            if _matches_where(chunk.metadata, where):
                scored.append(RetrievedChunk(chunk.text, dict(chunk.metadata), _cosine_similarity(query_vector, vector)))
        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]


class ChromaVectorStore:
    """Thin wrapper around a local persistent Chroma database."""

    def __init__(self, db_dir: Path, embedding_model: str, use_sentence_transformers: bool = True) -> None:
        """Create a Chroma client that stores data under db_dir."""
        try:
            import chromadb
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise RuntimeError("chromadb is required for persistent vector storage.") from exc

        ensure_directory(db_dir)
        self.client = chromadb.PersistentClient(path=str(db_dir))
        self.embedding_function = get_embedding_function(embedding_model, use_sentence_transformers)

    def rebuild_collection(self, collection_name: str, chunks: list[TextChunk]) -> int:
        """Delete and recreate a subject collection with the provided chunks."""
        try:
            self.client.delete_collection(collection_name)
        except Exception:
            pass
        collection = self.client.get_or_create_collection(name=collection_name, embedding_function=self.embedding_function)
        if not chunks:
            return 0
        ids = [str(chunk.metadata.get("chunk_id", f"{collection_name}-{index}")) for index, chunk in enumerate(chunks)]
        collection.add(ids=ids, documents=[chunk.text for chunk in chunks], metadatas=[dict(chunk.metadata) for chunk in chunks])
        return len(chunks)

    def query(self, collection_name: str, question: str, top_k: int = 4, where: dict | None = None) -> list[RetrievedChunk]:
        """Query one Chroma collection and return readable results."""
        try:
            collection = self.client.get_collection(collection_name, embedding_function=self.embedding_function)
        except Exception:
            return []
        result = collection.query(query_texts=[question], n_results=top_k, where=where)
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        retrieved: list[RetrievedChunk] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            score = 1.0 / (1.0 + float(distance))
            retrieved.append(RetrievedChunk(text=document, metadata=dict(metadata or {}), score=score))
        return retrieved
