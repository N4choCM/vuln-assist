"""Tests for Phase 5 context building and grounded response generation."""

from __future__ import annotations

import pytest

from services.response_generator.config import ResponseGeneratorConfig
from services.response_generator.context_builder import build_context
from services.response_generator.fallback import format_retrieval_reply
from services.response_generator.generator import ResponseGenerator


LOG4SHELL_RETRIEVAL: dict[str, object] = {
    "intent": "CVE_LOOKUP",
    "source": "nvd_live",
    "cves": [
        {
            "cve_id": "CVE-2021-44228",
            "description": "Apache Log4j2 JNDI injection vulnerability.",
            "cvss_score": 10.0,
            "severity": "CRITICAL",
            "products": ["Apache Log4j"],
            "versions": ["2.0"],
        }
    ],
    "mitre_techniques": [
        {"technique_id": "T1190", "name": "Exploit Public-Facing Application"},
    ],
    "errors": [],
    "raw_count": 1,
}


def test_context_builder_includes_cve_and_mitre() -> None:
    context = build_context(LOG4SHELL_RETRIEVAL)
    assert "CVE-2021-44228" in context
    assert "CVSS 10.0" in context
    assert "T1190" in context
    assert "nvd_live" in context


def test_fallback_cve_lookup_includes_techniques() -> None:
    reply = format_retrieval_reply("CVE_LOOKUP", LOG4SHELL_RETRIEVAL)
    assert "CVE-2021-44228" in reply
    assert "Exploit Public-Facing Application" in reply


def test_fallback_reports_empty_results() -> None:
    reply = format_retrieval_reply("PRODUCT_SEARCH", {"cves": [], "errors": []})
    assert reply == "No matching vulnerabilities were found."


class _StubLLM:
    def complete(self, *, system: str, user: str) -> str:
        assert "VulnAssist" in system
        assert "CVE-2021-44228" in user
        return "Log4Shell is a critical remote code execution flaw in Apache Log4j."


def test_generator_uses_stub_llm() -> None:
    config = ResponseGeneratorConfig(
        enabled=True,
        provider="ollama",
        temperature=0.1,
        max_tokens=300,
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model="llama3.2",
        timeout_seconds=30.0,
    )
    generator = ResponseGenerator(config=config, llm_client=_StubLLM())
    reply = generator.generate(
        "What is CVE-2021-44228?",
        "CVE_LOOKUP",
        LOG4SHELL_RETRIEVAL,
    )
    assert "Log4Shell" in reply


def test_generator_falls_back_when_llm_disabled() -> None:
    config = ResponseGeneratorConfig(
        enabled=False,
        provider="none",
        temperature=0.1,
        max_tokens=300,
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model="llama3.2",
        timeout_seconds=30.0,
    )
    generator = ResponseGenerator(config=config, llm_client=None)
    reply = generator.generate(
        "What is CVE-2021-44228?",
        "CVE_LOOKUP",
        LOG4SHELL_RETRIEVAL,
    )
    assert "CVE-2021-44228" in reply
    assert "Apache Log4j2" in reply


class _FailingLLM:
    def complete(self, *, system: str, user: str) -> str:
        raise ConnectionError("Ollama unavailable")


def test_generator_falls_back_on_llm_error() -> None:
    config = ResponseGeneratorConfig(
        enabled=True,
        provider="ollama",
        temperature=0.1,
        max_tokens=300,
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model="llama3.2",
        timeout_seconds=30.0,
    )
    generator = ResponseGenerator(config=config, llm_client=_FailingLLM())
    reply = generator.generate(
        "What is CVE-2021-44228?",
        "CVE_LOOKUP",
        LOG4SHELL_RETRIEVAL,
    )
    assert "CVE-2021-44228" in reply


@pytest.mark.parametrize(
    "provider",
    ["none"],
)
def test_build_llm_client_returns_none_when_disabled(provider: str) -> None:
    from services.response_generator.config import build_llm_client

    config = ResponseGeneratorConfig(
        enabled=False,
        provider=provider,
        temperature=0.1,
        max_tokens=300,
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model="llama3.2",
        timeout_seconds=30.0,
    )
    assert build_llm_client(config) is None
