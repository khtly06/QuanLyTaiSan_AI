"""LLM service abstraction for different providers."""

from __future__ import annotations

import os

import requests


class LLMProviderError(RuntimeError):
    """A safe, classified error returned by the configured provider."""

    _USER_MESSAGES = {
        "quota": (
            "AI chưa thể trả lời vì tài khoản nhà cung cấp đã hết hạn mức hoặc "
            "credit. Quản trị viên cần kiểm tra billing/quota của API."
        ),
        "authentication": (
            "AI chưa thể trả lời vì nhà cung cấp từ chối xác thực API key. "
            "Quản trị viên cần kiểm tra cấu hình key."
        ),
        "access": (
            "API key hiện không có quyền sử dụng dịch vụ hoặc mô hình AI này."
        ),
        "model_or_endpoint": (
            "Cấu hình mô hình hoặc endpoint AI không hợp lệ."
        ),
        "rate_limit": (
            "AI đang nhận quá nhiều yêu cầu. Vui lòng chờ rồi thử lại."
        ),
        "unavailable": (
            "Nhà cung cấp AI tạm thời không khả dụng. Vui lòng thử lại sau."
        ),
        "rejected": (
            "Nhà cung cấp AI từ chối yêu cầu. Vui lòng kiểm tra cấu hình dịch vụ."
        ),
    }

    def __init__(self, category):
        self.category = category
        self.user_message = self._USER_MESSAGES.get(
            category, self._USER_MESSAGES["rejected"]
        )
        super().__init__(self.user_message)


class LLMService:
    """Call an OpenAI-compatible chat-completions API."""

    def __init__(
        self,
        api_key=None,
        model="gpt-3.5-turbo",
        base_url=None,
        timeout=None,
        max_prompt_chars=None,
    ):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = model or os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.base_url = base_url or os.getenv(
            "LLM_API_BASE_URL",
            "https://api.openai.com/v1/chat/completions",
        )
        self.timeout = float(
            timeout if timeout is not None else os.getenv("LLM_TIMEOUT_SECONDS", "30")
        )
        self.max_prompt_chars = int(
            max_prompt_chars
            if max_prompt_chars is not None
            else os.getenv("LLM_MAX_PROMPT_CHARS", "12000")
        )

    def _has_valid_key(self):
        """Return True when the API key is configured and not a placeholder."""
        placeholder_values = {
            "",
            "your_api_key_here",
            "change_me",
            "placeholder",
            "demo",
            "example",
            "test",
        }
        return bool(self.api_key) and self.api_key.lower() not in placeholder_values

    @staticmethod
    def _provider_error_category(response):
        """Classify an HTTP error without exposing the provider response body."""
        status_code = getattr(response, "status_code", 0)
        error_code = ""
        error_type = ""
        try:
            payload = response.json()
        except (AttributeError, ValueError):
            payload = {}
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                error_code = error.get("code", "")
                error_type = error.get("type", "")
        if not isinstance(error_code, str):
            error_code = ""
        if not isinstance(error_type, str):
            error_type = ""

        if status_code == 429:
            if error_code in {"insufficient_quota", "credit_balance_exhausted"} or (
                error_type == "insufficient_quota"
            ):
                return "quota"
            return "rate_limit"
        if status_code == 401:
            return "authentication"
        if status_code == 403:
            return "access"
        if status_code == 404:
            return "model_or_endpoint"
        if status_code >= 500:
            return "unavailable"
        return "rejected"

    def generate(self, prompt, system_prompt=None):
        """Send the prompt to the configured provider and return the answer."""
        if not self._has_valid_key():
            raise ValueError("LLM_API_KEY is missing or placeholder. Please set the key in .env.")

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")
        if system_prompt is not None and (
            not isinstance(system_prompt, str) or not system_prompt.strip()
        ):
            raise ValueError("System prompt must be a non-empty string when provided.")
        if len(prompt) > self.max_prompt_chars:
            raise ValueError(
                f"Prompt exceeds the configured limit of {self.max_prompt_chars} characters."
            )
        if self.timeout <= 0:
            raise ValueError("LLM_TIMEOUT_SECONDS must be greater than zero.")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = requests.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            raise RuntimeError("The LLM provider request timed out.") from exc
        except requests.HTTPError as exc:
            error_response = exc.response
            if error_response is None:
                raise RuntimeError("The LLM provider request failed.") from exc
            category = self._provider_error_category(error_response)
            raise LLMProviderError(category) from exc
        except requests.RequestException as exc:
            raise RuntimeError("The LLM provider request failed.") from exc

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RuntimeError("The LLM provider returned an invalid response.") from exc
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("The LLM provider returned an empty response.")
        return content.strip()
