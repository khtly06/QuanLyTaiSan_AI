"""Integration-style tests for the RAG pipeline."""

from app.rag.document_loader import DocumentLoader
from app.rag.document_chunker import DocumentChunker
from app.rag.embedding_service import EmbeddingService
from app.rag.prompt_builder import PromptBuilder
from app.rag.rag_service import RAGService
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore
from app.llm.llm_service import LLMService


def test_document_loader_supports_markdown_and_text():
    """The loader should read real text from supported files."""
    loader = DocumentLoader("data/documents/policy.md")
    text = loader.load()
    assert "tài sản" in text.lower()
    assert "trường học" in text.lower()


def test_rag_pipeline_builds_grounded_answer_with_context():
    """The pipeline should retrieve relevant context and answer grounded in it."""
    documents = [
        {
            "id": "policy_1",
            "source_name": "school_policy.md",
            "content": (
                "Quy định quản lý tài sản trường học: Tài sản cố định phải được ghi "
                "nhận và kiểm kê định kỳ mỗi quý. Mỗi bộ phận phải chịu trách nhiệm "
                "về tài sản được giao."
            ),
        },
        {
            "id": "policy_2",
            "source_name": "inventory_policy.md",
            "content": (
                "Đối với tài sản hỏng, lãnh đạo bộ phận phải lập biên bản xử lý trong "
                "vòng 5 ngày làm việc."
            ),
        },
    ]
    vector_store = VectorStore()
    vector_store.add_documents(documents)

    retriever = Retriever(vector_store)
    context = retriever.retrieve("kiểm kê tài sản định kỳ", top_k=2)
    prompt = PromptBuilder.build_prompt("kiểm kê tài sản định kỳ", context)
    assert "kiểm kê" in prompt.lower()

    rag_service = RAGService(retriever, LLMService(api_key="demo-key"))
    result = rag_service.answer_question("kiểm kê tài sản định kỳ")
    assert "answer" in result
    assert "sources" in result
    assert result["sources"]

    embeddings = EmbeddingService()
    vectors = embeddings.embed_documents(documents)
    assert len(vectors) == 2
    assert len(vectors[0]) > 0

    chunker = DocumentChunker(chunk_size=80, chunk_overlap=20)
    parts = chunker.chunk_text(documents[0]["content"], "school_policy.md")
    assert len(parts) >= 1
