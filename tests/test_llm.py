"""Tests for the LLM service wrapper."""

from app.llm.llm_service import LLMService


def test_llm_service_missing_key_raises():
    """The service should fail clearly when no API key is configured."""
    service = LLMService(api_key="")

    try:
        service.generate("Question")
        assert False, "Expected ValueError for missing API key."
    except ValueError:
        assert True
