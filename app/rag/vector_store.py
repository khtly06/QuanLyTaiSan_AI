"""Vector store abstraction for document embeddings."""

from __future__ import annotations

import os
import re

from app.rag.embedding_service import EmbeddingService


class VectorStore:
    """Simple in-memory vector store for demo purposes."""

    def __init__(self, storage_path=None, embedding_service=None):
        self.storage_path = storage_path or os.path.join(
            os.getcwd(), "vector_db"
        )
        self.embedding_service = embedding_service or EmbeddingService()
        self.documents = []

    @staticmethod
    def _vector_dot_product(left, right):
        """Compute the dot product of two vectors."""
        if not left or not right:
            return 0.0
        length = min(len(left), len(right))
        return sum(left[index] * right[index] for index in range(length))

    @staticmethod
    def _keyword_overlap(query_text, document_text):
        """Count shared keywords between the question and the document."""
        query_tokens = set(re.findall(r"\w+", str(query_text).lower()))
        document_tokens = set(re.findall(r"\w+", str(document_text).lower()))
        if not query_tokens or not document_tokens:
            return 0
        return len(query_tokens & document_tokens)

    def add_documents(self, documents):
        """Add documents to the vector store."""
        for document in documents:
            item = dict(document)
            if "embedding" not in item:
                item["embedding"] = self.embedding_service.embed_text(
                    item.get("content", "")
                )
            self.documents.append(item)
        return len(documents)

    def similarity_search(self, query_text, top_k=4):
        """Return the most relevant documents by semantic + keyword score."""
        if not query_text or not str(query_text).strip():
            return []

        query_lower = str(query_text).lower()
        query_embedding = self.embedding_service.embed_text(query_text)
        scored = []

        for document in self.documents:
            content = str(document.get("content", ""))
            document_embedding = document.get("embedding") or self.embedding_service.embed_text(content)
            semantic_score = self._vector_dot_product(query_embedding, document_embedding)
            keyword_score = self._keyword_overlap(query_lower, content) * 2
            source_bonus = 1 if document.get("source_name") else 0
            score = semantic_score + keyword_score + source_bonus
            scored.append({"document": document, "score": float(score)})

        scored.sort(key=lambda item: item["score"], reverse=True)
        return [item["document"] for item in scored[:top_k]]

    def persist(self):
        """Persist the vector database if supported."""
        os.makedirs(self.storage_path, exist_ok=True)
        return self.storage_path
