"""Session and outcome structures for dialogue management."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DialogueSession:
    """Mutable per-conversation state handled by repositories.

    Tracks accumulated slots from NER interpretations across turns until the dialogue
    can hand off to the query builder in a later phase.
    """

    active_intent: str | None = None
    slots: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialize for debugging and API payloads."""

        return {
            "active_intent": self.active_intent,
            "slots": dict(self.slots),
        }


@dataclass(frozen=True)
class DialogueOutcome:
    """One assistant turn shaped by NLU inputs and finite-state policy."""

    reply: str
    state: str
    slots: dict[str, str]
    intent: str
    ready_for_external_query: bool
    blocked_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "reply": self.reply,
            "state": self.state,
            "slots": dict(self.slots),
            "intent": self.intent,
            "ready_for_external_query": self.ready_for_external_query,
            "blocked_reason": self.blocked_reason,
        }


# Human-readable identifiers for telemetry and debugging; not persisted as enums.
STATE_IDLE = "idle"
STATE_CLARIFYING = "clarifying"
STATE_READY = "ready"
STATE_GENERAL = "general"
