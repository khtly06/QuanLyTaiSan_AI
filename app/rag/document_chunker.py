"""Chunking logic for the RAG document pipeline."""

from __future__ import annotations

import re


class DocumentChunker:
    """Split text into chunks with metadata."""

    def __init__(self, chunk_size=500, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _make_chunk(self, content, source_name, index):
        """Build a chunk record with metadata."""
        return {
            "id": f"{source_name}_{index}",
            "source_name": source_name,
            "content": content.strip(),
            "page": None,
        }

    def chunk_text(self, text, source_name="document"):
        """Split text into overlapping chunks and attach metadata."""
        if not text or not text.strip():
            return []

        cleaned = re.sub(r"\s+", " ", text).strip()
        chunks = []
        start = 0
        index = 0

        while start < len(cleaned):
            end = min(start + self.chunk_size, len(cleaned))
            chunk_text = cleaned[start:end]

            if end < len(cleaned):
                last_space = chunk_text.rfind(" ")
                if last_space > self.chunk_size * 0.6:
                    end = start + last_space
                    chunk_text = cleaned[start:end]

            chunks.append(self._make_chunk(chunk_text, source_name, index))
            index += 1

            if end >= len(cleaned):
                break
            start = max(0, end - self.chunk_overlap)

        return chunks
