"""RAG orchestration service."""

from __future__ import annotations

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
        answer = self.llm_service.generate(prompt)
        return {
            "answer": answer,
            "sources": [
                item.get("source_name", "unknown") for item in context
            ],
        }
