"""Dataset domain models shared by generation, annotation, and writers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EntityValue:
    """Entity value selected for injection into a generated query."""

    entity_type: str
    value: str


@dataclass(frozen=True)
class EntitySpan:
    """Character-level entity mention in a generated query."""

    entity_type: str
    value: str
    start: int
    end: int

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.entity_type,
            "value": self.value,
            "start": self.start,
            "end": self.end,
        }


@dataclass(frozen=True)
class TokenAnnotation:
    """Token-level BIO annotation."""

    token: str
    tag: str
    start: int
    end: int


@dataclass(frozen=True)
class BIOAnnotation:
    """Result of BIO annotation for one generated query."""

    tokens: list[TokenAnnotation]
    entities: list[EntitySpan]


@dataclass(frozen=True)
class DatasetSample:
    """One generated NLU training sample."""

    text: str
    intent: str
    entities: list[EntitySpan]
    tokens: list[TokenAnnotation]

    def to_intent_record(self) -> dict[str, object]:
        # Intent JSON keeps token-level BIO data out; that belongs in the CoNLL file.
        return {
            "text": self.text,
            "intent": self.intent,
            "entities": [entity.to_dict() for entity in self.entities],
        }
