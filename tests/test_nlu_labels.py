from __future__ import annotations

from data.dataset.labels import ENTITY_TYPES, INTENTS
from services.nlu.labels import BIO_LABELS, INTENT_LABELS, build_bio_labels


def test_bio_labels_are_generated_from_shared_entity_types():
    labels = build_bio_labels()

    assert labels[0] == "O"
    assert len(labels) == 1 + (2 * len(ENTITY_TYPES))
    for entity_type in ENTITY_TYPES:
        assert f"B-{entity_type}" in labels
        assert f"I-{entity_type}" in labels


def test_intent_labels_reuse_dataset_inventory():
    assert INTENT_LABELS == INTENTS
    assert "B-CVE_ID" in BIO_LABELS
