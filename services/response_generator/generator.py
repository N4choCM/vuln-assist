"""Grounded natural-language reply generation from Phase 4 retrieval payloads."""

from __future__ import annotations

import logging
from typing import Protocol

from integrations.llm.client import LLMClient
from services.response_generator.config import (
    ResponseGeneratorConfig,
    build_llm_client,
    load_response_generator_config,
)
from services.response_generator.context_builder import build_context
from services.response_generator.fallback import format_retrieval_reply
from services.response_generator.prompts import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Transform structured retrieval data into a user-facing reply."""

    def __init__(
        self,
        config: ResponseGeneratorConfig | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self._config = config or load_response_generator_config()
        self._llm = llm_client if llm_client is not None else build_llm_client(self._config)

    def generate(self, user_query: str, intent: str, retrieval: dict[str, object]) -> str:
        """Return an LLM reply when enabled; otherwise use deterministic fallback."""

        fallback = format_retrieval_reply(intent, retrieval)
        if not self._config.enabled or self._llm is None:
            return fallback

        context = build_context(retrieval)
        user_prompt = build_user_prompt(
            user_query=user_query,
            intent=intent,
            context=context,
        )

        try:
            return self._llm.complete(system=SYSTEM_PROMPT, user=user_prompt)
        except Exception as exc:  # noqa: BLE001 — degrade to template on any LLM failure
            logger.warning("LLM generation failed, using fallback: %s", exc)
            return fallback


class ResponseGeneratorProtocol(Protocol):
    """Structural typing hook for mocking generation in tests."""

    def generate(self, user_query: str, intent: str, retrieval: dict[str, object]) -> str:
        ...
