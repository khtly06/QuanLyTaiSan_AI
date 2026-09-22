"""LLM service abstraction for different providers."""

from __future__ import annotations

import os


class LLMService:
    """Thin wrapper around an external LLM API provider."""

    def __init__(self, api_key=None, provider="openai", model="gpt-3.5-turbo"):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("LLM_API_KEY", "")
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai")
        self.model = model or os.getenv("LLM_MODEL", "gpt-3.5-turbo")

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

    def generate(self, prompt):
        """Send the prompt to the configured provider and return the answer."""
        if not self._has_valid_key():
            raise ValueError("LLM_API_KEY is missing or placeholder. Please set the key in .env.")

        return (
            "Demo AI response. Replace this with a real API call to the selected "
            f"provider: {self.provider}, model: {self.model}.\n\nPrompt preview: "
            f"{prompt[:200]}"
        )
