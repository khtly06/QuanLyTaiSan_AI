"""Embedding service using a pluggable embedding model."""

from __future__ import annotations

import hashlib
import re

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover
    SentenceTransformer = None


class EmbeddingService:
    """Generate embeddings for text chunks."""

    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None

        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception:  # pragma: no cover
                self.model = None

    def _fallback_embedding(self, text):
        """Generate a deterministic embedding without external ML dependencies."""
        tokens = re.findall(r"\w+", str(text).lower())
        if not tokens:
            return [0.0] * 32

        vector = [0.0] * 32
        unique_tokens = sorted(set(tokens))[:32]
        for index, token in enumerate(unique_tokens):
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            vector[index] = float(int(digest[:8], 16) % 1000) / 1000.0
        return vector

    def embed_text(self, text):
        """Return a vector representation for a text input."""
        if not text or not str(text).strip():
            return []

        if self.model is not None:
            vector = self.model.encode(str(text), normalize_embeddings=True)
            return [float(value) for value in vector.tolist()]

        return self._fallback_embedding(text)

    def embed_documents(self, documents):
        """Return embeddings for a list of documents."""
        return [self.embed_text(item.get("content", "")) for item in documents]
