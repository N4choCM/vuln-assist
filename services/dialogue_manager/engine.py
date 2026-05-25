"""Finite-state dialogue policy rooted in `.cursor/rules/domain.mdc` intents."""

from __future__ import annotations

from services.dialogue_manager.models import (
    STATE_CLARIFYING,
    STATE_GENERAL,
    STATE_READY,
    DialogueOutcome,
    DialogueSession,
)
from services.nlu.models import NLUResult

# Mirrors domain intents: CVE_LOOKUP, CVSS_QUERY, PRODUCT_SEARCH, VERSION_SEARCH,
# SEVERITY_FILTER, GENERAL_QUERY.
KNOWN_INTENTS: frozenset[str] = frozenset(
    {
        "CVE_LOOKUP",
        "CVSS_QUERY",
        "PRODUCT_SEARCH",
        "VERSION_SEARCH",
        "SEVERITY_FILTER",
        "GENERAL_QUERY",
    }
)

_REQUIRED_SLOTS_BY_INTENT: dict[str, tuple[str, ...]] = {
    "CVE_LOOKUP": ("CVE_ID",),
    "CVSS_QUERY": ("CVE_ID",),
    "PRODUCT_SEARCH": ("PRODUCT",),
    # Product disambiguates which stream is being queried when only a bare version appears.
    "VERSION_SEARCH": ("PRODUCT", "VERSION"),
    "SEVERITY_FILTER": ("SEVERITY",),
}

_CLARIFICATION_TEMPLATES: dict[str, str] = {
    "CVE_ID": "Please specify a CVE identifier (for example CVE-2021-44228).",
    "PRODUCT": "Which product should I filter on?",
    "VERSION": "Which product version matters for this query?",
    "SEVERITY": "Which severity tier should be used as a filter?",
}


class DialogueEngine:
    """Stateful policy translating NLU into slot updates and scripted replies."""

    def process_turn(self, session: DialogueSession, nlu: NLUResult) -> DialogueOutcome:
        """Apply one NLU result to ``session`` in place and return the assistant outcome."""

        intent = nlu.intent if nlu.intent in KNOWN_INTENTS else "GENERAL_QUERY"
        self._merge_entities(session, nlu)

        session.active_intent = intent

        # General questions never block on slots and never trigger external lookups.
        if intent == "GENERAL_QUERY":
            return DialogueOutcome(
                reply=(
                    "I can help investigate CVE identifiers, severity filters, CVSS "
                    "details, products, or versions once you anchor the question with those "
                    "entities."
                ),
                state=STATE_GENERAL,
                slots=dict(session.slots),
                intent=intent,
                ready_for_external_query=False,
                blocked_reason=None,
            )

        required = self._requirements_for(intent)
        missing_slot = next((slot for slot in required if not session.slots.get(slot)), None)
        if missing_slot is not None:
            clarification = _CLARIFICATION_TEMPLATES.get(
                missing_slot,
                "I need additional details before I can continue.",
            )
            return DialogueOutcome(
                reply=clarification,
                state=STATE_CLARIFYING,
                slots=dict(session.slots),
                intent=intent,
                ready_for_external_query=False,
                blocked_reason=None,
            )

        return DialogueOutcome(
            reply="Retrieving vulnerability data...",
            state=STATE_READY,
            slots=dict(session.slots),
            intent=intent,
            ready_for_external_query=True,
            blocked_reason=None,
        )

    def _requirements_for(self, intent: str) -> tuple[str, ...]:
        slots = _REQUIRED_SLOTS_BY_INTENT.get(intent, ())
        return slots

    @staticmethod
    def _merge_entities(session: DialogueSession, nlu: NLUResult) -> None:
        """Overlay highest-confidence interpretations for duplicate entity types."""

        best_by_type: dict[str, tuple[str, float]] = {}
        for entity in sorted(nlu.entities, key=lambda ent: (-ent.confidence, ent.start)):
            current = best_by_type.get(entity.entity_type)
            if current is None or entity.confidence >= current[1]:
                best_by_type[entity.entity_type] = (entity.value, entity.confidence)

        merged = dict(session.slots)
        for entity_type, (value, _confidence) in best_by_type.items():
            merged[entity_type] = value
        session.slots.clear()
        session.slots.update(merged)
