"""LLM provider abstraction. Any OpenAI-compatible endpoint works (OpenAI, Groq, OpenRouter, Ollama)."""
from typing import Protocol

import httpx

from .config import Settings


class LLMError(RuntimeError):
    """Raised when the upstream model provider fails."""


class LLMClient(Protocol):
    def complete(self, messages: list[dict]) -> str: ...


class EchoClient:
    """Offline provider so the app is demoable without any API key."""

    def complete(self, messages: list[dict]) -> str:
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"(echo mode - set LLM_PROVIDER=openai-compatible for real answers) You said: {last_user}"


class OpenAICompatibleClient:
    def __init__(self, settings: Settings):
        if not settings.llm_api_key:
            raise LLMError("LLM_API_KEY is required for the openai-compatible provider")
        self.settings = settings

    def complete(self, messages: list[dict]) -> str:
        s = self.settings
        try:
            resp = httpx.post(
                f"{s.llm_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {s.llm_api_key}"},
                json={"model": s.llm_model, "messages": messages},
                timeout=s.llm_timeout_seconds,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except httpx.HTTPError as exc:
            raise LLMError(f"Upstream model request failed: {exc}") from exc
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMError("Unexpected response format from model provider") from exc


def build_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "openai-compatible":
        return OpenAICompatibleClient(settings)
    if settings.llm_provider == "echo":
        return EchoClient()
    raise LLMError(f"Unknown LLM_PROVIDER: {settings.llm_provider!r}")
