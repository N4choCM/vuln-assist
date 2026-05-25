"""Label mappings for intent classification and BIO NER."""

from __future__ import annotations

from data.dataset.labels import ENTITY_TYPES, INTENTS


INTENT_LABELS: tuple[str, ...] = INTENTS


def build_bio_labels(entity_types: tuple[str, ...] = ENTITY_TYPES) -> tuple[str, ...]:
    """Build BIO labels from the shared project entity inventory."""

    labels = ["O"]
    for entity_type in entity_types:
        labels.extend((f"B-{entity_type}", f"I-{entity_type}"))
    return tuple(labels)


BIO_LABELS: tuple[str, ...] = build_bio_labels()

INTENT_LABEL_TO_ID: dict[str, int] = {
    label: index for index, label in enumerate(INTENT_LABELS)
}
INTENT_ID_TO_LABEL: dict[int, str] = {
    index: label for label, index in INTENT_LABEL_TO_ID.items()
}

BIO_LABEL_TO_ID: dict[str, int] = {label: index for index, label in enumerate(BIO_LABELS)}
BIO_ID_TO_LABEL: dict[int, str] = {
    index: label for label, index in BIO_LABEL_TO_ID.items()
}
