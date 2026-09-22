"""Document loading utilities for the RAG pipeline."""

from __future__ import annotations

from pathlib import Path

try:
    from PyPDF2 import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None

try:
    from docx import Document as DocxDocument
except ImportError:  # pragma: no cover
    DocxDocument = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class DocumentLoader:
    """Load text content from supported document files."""

    def __init__(self, file_path):
        self.file_path = self._resolve_path(file_path)

    def _resolve_path(self, file_path):
        """Resolve relative paths against the project root and common data folders."""
        path = Path(file_path)
        if path.is_absolute():
            return path

        candidates = [
            Path.cwd() / path,
            PROJECT_ROOT / path,
            PROJECT_ROOT / "data" / "documents" / path.name,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate

        return PROJECT_ROOT / path

    def load(self):
        """Read and return the text content of a supported file."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        suffix = self.file_path.suffix.lower()

        if suffix in {".txt", ".md", ".markdown"}:
            return self.file_path.read_text(encoding="utf-8")

        if suffix == ".pdf":
            if PdfReader is None:
                return (
                    "PDF parsing is unavailable in the current environment. "
                    "Install PyPDF2 to enable full PDF processing."
                )
            reader = PdfReader(str(self.file_path))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            return "\n\n".join(pages)

        if suffix == ".docx":
            if DocxDocument is None:
                return (
                    "DOCX parsing is unavailable in the current environment. "
                    "Install python-docx to enable full DOCX processing."
                )
            document = DocxDocument(str(self.file_path))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)

        raise ValueError(f"Unsupported file type: {suffix}")
