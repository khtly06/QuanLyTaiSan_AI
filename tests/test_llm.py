"""Tests for the OpenAI-compatible LLM service wrapper."""

import pytest
import requests

from app.llm.llm_service import LLMService


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError("provider error")
            error.response = self
            raise error

    def json(self):
        return self.payload


def test_llm_service_missing_key_raises():
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        LLMService(api_key="").generate("Question")


def test_llm_service_sends_bounded_request_and_returns_provider_text(monkeypatch):
    request = {}

    def fake_post(url, **kwargs):
        request["url"] = url
        request.update(kwargs)
        return FakeResponse(
            {"choices": [{"message": {"content": "  Phân tích dựa trên dữ liệu.  "}}]}
        )

    monkeypatch.setattr("app.llm.llm_service.requests.post", fake_post)
    service = LLMService(
        api_key="configured-test-key",
        model="test-model",
        base_url="https://llm.example.invalid/chat",
        timeout=2,
    )

    answer = service.generate("Test prompt")

    assert answer == "Phân tích dựa trên dữ liệu."
    assert request["url"] == "https://llm.example.invalid/chat"
    assert request["headers"]["Authorization"] == "Bearer configured-test-key"
    assert request["json"]["model"] == "test-model"
    assert request["timeout"] == 2


def test_llm_service_sends_system_and_user_prompts_separately(monkeypatch):
    request = {}

    def fake_post(url, **kwargs):
        request.update(kwargs)
        return FakeResponse(
            {"choices": [{"message": {"content": "Response"}}]}
        )

    monkeypatch.setattr("app.llm.llm_service.requests.post", fake_post)
    service = LLMService(api_key="configured-test-key")

    service.generate("User prompt", system_prompt="System prompt")

    assert request["json"]["messages"] == [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "User prompt"},
    ]


def test_llm_service_rejects_oversized_prompt_before_network_call(monkeypatch):
    def fail_if_called(*args, **kwargs):
        pytest.fail("No provider request should be made for an oversized prompt.")

    monkeypatch.setattr("app.llm.llm_service.requests.post", fail_if_called)
    service = LLMService(api_key="configured-test-key", max_prompt_chars=4)

    with pytest.raises(ValueError, match="configured limit"):
        service.generate("12345")


def test_llm_service_does_not_expose_provider_error_details(monkeypatch):
    def fail_request(*args, **kwargs):
        raise requests.Timeout("secret-bearing request context")

    monkeypatch.setattr("app.llm.llm_service.requests.post", fail_request)
    service = LLMService(api_key="configured-test-key")

    with pytest.raises(RuntimeError, match="timed out") as error:
        service.generate("Question")

    assert "secret-bearing" not in str(error.value)


def test_llm_service_rejects_malformed_provider_response(monkeypatch):
    monkeypatch.setattr(
        "app.llm.llm_service.requests.post",
        lambda *args, **kwargs: FakeResponse({"choices": []}),
    )
    service = LLMService(api_key="configured-test-key")

    with pytest.raises(RuntimeError, match="invalid response"):
        service.generate("Question")


def test_llm_service_classifies_exhausted_provider_quota_without_exposing_body(
    monkeypatch,
):
    from app.llm.llm_service import LLMProviderError

    monkeypatch.setattr(
        "app.llm.llm_service.requests.post",
        lambda *args, **kwargs: FakeResponse(
            {
                "error": {
                    "type": "insufficient_quota",
                    "code": "credit_balance_exhausted",
                    "message": "Sensitive provider detail",
                }
            },
            status_code=429,
        ),
    )
    service = LLMService(api_key="configured-test-key")

    with pytest.raises(LLMProviderError) as error:
        service.generate("Question")

    assert error.value.category == "quota"
    assert "hết hạn mức" in error.value.user_message
    assert "Sensitive provider detail" not in str(error.value)
