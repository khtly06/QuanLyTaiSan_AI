"""Retriever component for the RAG pipeline."""

from __future__ import annotations


class Retriever:
    """Retrieve relevant chunks for a user question."""

    def __init__(self, vector_store):
        self.vector_store = vector_store

    def retrieve(self, question, top_k=4):
        """Return top matching chunks for a question."""
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        return self.vector_store.similarity_search(question, top_k=top_k)
