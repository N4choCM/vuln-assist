"""Wrap the Phase 5 `ResponseGenerator` for backend orchestration."""

from __future__ import annotations

from typing import Protocol

from services.response_generator.generator import ResponseGenerator


class ResponseGeneratorProtocol(Protocol):
    """Structural typing hook for mocking generation in isolated tests."""

    def generate(self, user_query: str, intent: str, retrieval: dict[str, object]) -> str:
        ...


class ResponseGeneratorRepository:
    """Thin façade over grounded LLM reply generation."""

    def __init__(self, generator: ResponseGenerator) -> None:
        self._generator = generator

    def generate(self, user_query: str, intent: str, retrieval: dict[str, object]) -> str:
        return self._generator.generate(user_query, intent, retrieval)
