"""Embedding functions for Chroma plus a tiny deterministic test fallback."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class HashEmbeddingFunction:
    """Small deterministic embedding function used for tests and dry runs."""

    dimension: int = 64

    def __call__(self, input: list[str]) -> list[list[float]]:  # Chroma expects the parameter name ``input``.
        """Return simple normalized vectors for a list of texts."""
        return [self.embed_text(text) for text in input]

    def embed_text(self, text: str) -> list[float]:
        """Embed text with hashed tokens so similar words overlap a little."""
        vector = [0.0] * self.dimension
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = digest[0] % self.dimension
            vector[index] += 1.0
        length = sum(value * value for value in vector) ** 0.5 or 1.0
        return [value / length for value in vector]


def get_embedding_function(model_name: str, prefer_sentence_transformers: bool = True):
    """Return a Sentence Transformer embedding function or the hash fallback."""
    if prefer_sentence_transformers:
        try:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

            return SentenceTransformerEmbeddingFunction(model_name=model_name)
        except Exception:
            # The fallback keeps the app testable when model packages or downloads are unavailable.
            return HashEmbeddingFunction()
    return HashEmbeddingFunction()

