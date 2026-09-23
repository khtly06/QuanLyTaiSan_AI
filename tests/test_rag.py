"""Tests for the RAG pipeline."""

from app.rag.document_loader import DocumentLoader
from app.rag.document_chunker import DocumentChunker


def test_load_document_from_text_file(tmp_path):
    """Verify a text file can be loaded."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("Nội quy quản lý tài sản trường học.", encoding="utf-8")

    loader = DocumentLoader(file_path)
    content = loader.load()

    assert "tài sản" in content.lower()


def test_chunk_document():
    """Verify a document can be chunked."""
    chunker = DocumentChunker(chunk_size=20, chunk_overlap=5)
    chunks = chunker.chunk_text("Đây là ví dụ về tài sản trường học.", "demo.txt")

    assert len(chunks) > 0
    assert chunks[0]["source_name"] == "demo.txt"
