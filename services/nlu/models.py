"""Small dataclasses shared by NLU training and prediction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntentSample:
    """One text sample for intent classification."""

    text: str
    intent: str


@dataclass(frozen=True)
class NERSample:
    """One tokenized sample with BIO tags for NER fine-tuning."""

    tokens: list[str]
    tags: list[str]
    split: str
    intent: str
    text: str


@dataclass(frozen=True)
class EntityPrediction:
    """Entity extracted from a user query by the NER model."""

    entity_type: str
    value: str
    start: int
    end: int
    confidence: float

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_type": self.entity_type,
            "value": self.value,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class NLUResult:
    """Structured output passed from NLU to later system layers."""

    text: str
    intent: str
    intent_confidence: float
    entities: list[EntityPrediction]

    def to_dict(self) -> dict[str, object]:
        return {
            "text": self.text,
            "intent": self.intent,
            "intent_confidence": self.intent_confidence,
            "entities": [entity.to_dict() for entity in self.entities],
        }
