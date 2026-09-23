"""Prompt builder for RAG answers."""

from __future__ import annotations


class PromptBuilder:
    """Construct system and user instructions for the LLM."""

    @staticmethod
    def build_prompt(question, context):
        """Create a prompt using system instructions and retrieved context."""
        if not context:
            return (
                "Bạn là trợ lý AI của trường học. "
                "Chỉ sử dụng thông tin trong tài liệu của nhà trường. "
                "Nếu không có thông tin phù hợp, trả lời: "
                "\"Không tìm thấy thông tin phù hợp trong tài liệu của nhà trường.\"\n\n"
                "Câu hỏi: "
                f"{question}"
            )

        context_text = "\n\n".join(
            f"Tài liệu: {item.get('source_name', 'unknown')}\n{item.get('content', '')}"
            for item in context
        )
        return (
            "Bạn là trợ lý AI của trường học. "
            "Chỉ ưu tiên sử dụng thông tin trong Context dưới đây. "
            "Nếu Context không đủ thông tin, hãy trả lời rõ ràng rằng không tìm thấy "
            "thông tin phù hợp trong tài liệu của nhà trường.\n\n"
            "Context:\n"
            f"{context_text}\n\n"
            "Câu hỏi: "
            f"{question}"
        )
