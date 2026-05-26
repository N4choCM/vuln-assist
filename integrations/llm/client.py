"""HTTP clients for external LLM providers (Ollama local runtime)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx


class LLMClient(Protocol):
    """Minimal chat completion interface for response generation."""

    def complete(self, *, system: str, user: str) -> str:
        ...


@dataclass(frozen=True)
class OllamaConfig:
    """Connection settings for a local Ollama instance."""

    base_url: str
    model: str
    temperature: float
    max_tokens: int
    timeout_seconds: float


class OllamaClient:
    """Call Ollama's /api/chat endpoint without cloud credentials."""

    def __init__(self, config: OllamaConfig) -> None:
        self._config = config

    def complete(self, *, system: str, user: str) -> str:
        payload: dict[str, Any] = {
            "model": self._config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": self._config.temperature,
                "num_predict": self._config.max_tokens,
            },
        }
        url = f"{self._config.base_url.rstrip('/')}/api/chat"
        with httpx.Client(timeout=self._config.timeout_seconds) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            body = response.json()

        message = body.get("message", {})
        if not isinstance(message, dict):
            raise ValueError("Ollama response missing message object")
        content = message.get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Ollama returned an empty completion")
        return content.strip()
