"""RAG orchestration service."""

from __future__ import annotations

from pathlib import Path

from app.rag.prompt_builder import PromptBuilder


class RAGService:
    """Coordinate document retrieval and answer generation."""

    def __init__(self, retriever, llm_service):
        self.retriever = retriever
        self.llm_service = llm_service

    def answer_question(self, question):
        """Retrieve relevant documents, build context, and generate answer."""
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        context = self.retriever.retrieve(question, top_k=4)
        prompt = PromptBuilder.build_prompt(question, context)
        system_prompt_path = (
            Path(__file__).resolve().parents[2] / "prompts" / "rag_system.md"
        )
        system_prompt = system_prompt_path.read_text(encoding="utf-8")
        answer = self.llm_service.generate(prompt, system_prompt=system_prompt)
        return {
            "answer": answer,
            "sources": [
                item.get("source_name", "unknown") for item in context
            ],
        }
