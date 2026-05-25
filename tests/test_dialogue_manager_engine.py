"""Tests deterministic dialogue transitions without Torch."""

from __future__ import annotations

import pytest

from services.dialogue_manager import DialogueEngine
from services.dialogue_manager.models import DialogueSession
from services.nlu.models import EntityPrediction, NLUResult


def _result(
    text: str,
    intent: str,
    *,
    entities: list[EntityPrediction] | None = None,
) -> NLUResult:
    confidence = 0.91
    return NLUResult(
        text=text,
        intent=intent,
        intent_confidence=confidence,
        entities=entities or [],
    )


@pytest.fixture(name="cve_entity")
def fixture_cve_entity() -> EntityPrediction:
    return EntityPrediction("CVE_ID", "CVE-2024-8888", 0, 14, confidence=0.93)


@pytest.fixture(name="engine")
def fixture_engine() -> DialogueEngine:
    return DialogueEngine()


def test_general_query_never_requires_slots(engine: DialogueEngine) -> None:
    session = DialogueSession()
    prediction = _result("Hello", "GENERAL_QUERY")

    outcome = engine.process_turn(session, prediction)

    assert outcome.state == "general"
    assert outcome.ready_for_external_query is False
    assert outcome.blocked_reason is None


def test_unknown_intent_fallback_to_general(engine: DialogueEngine) -> None:
    session = DialogueSession()
    prediction = _result("ambiguous text", intent="UNSUPPORTED_DUMMY")

    outcome = engine.process_turn(session, prediction)

    assert outcome.intent == "GENERAL_QUERY"
    assert outcome.state == "general"


def test_cvss_requires_cve_id(engine: DialogueEngine, cve_entity: EntityPrediction) -> None:
    session = DialogueSession()
    incomplete = _result("tell me severity", intent="CVSS_QUERY")
    clarified = engine.process_turn(session, incomplete)

    assert clarified.state == "clarifying"
    assert clarified.ready_for_external_query is False

    follow_up = _result("CVE question", intent="CVSS_QUERY", entities=[cve_entity])
    ready = engine.process_turn(session, follow_up)

    assert ready.state == "ready"
    assert ready.ready_for_external_query is True
    assert ready.blocked_reason == "integrations_pending"
    assert session.slots["CVE_ID"] == cve_entity.value


def test_missing_product_version_pair(engine: DialogueEngine) -> None:
    """VERSION_SEARCH mandates both PRODUCT and VERSION slots."""

    session = DialogueSession()
    prediction = _result(
        "Need info",
        intent="VERSION_SEARCH",
        entities=[EntityPrediction("VERSION", "1.9", 0, 5, confidence=0.9)],
    )

    outcome = engine.process_turn(session, prediction)

    assert outcome.ready_for_external_query is False
