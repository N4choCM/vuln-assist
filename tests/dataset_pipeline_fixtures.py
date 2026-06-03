"""Shared fixtures for Phase 1 dataset pipeline unit tests."""

from __future__ import annotations

from data.dataset.bio_annotator import BIOAnnotator
from data.dataset.labels import INTENTS
from data.dataset.models import DatasetSample, EntitySpan, EntityValue, TokenAnnotation
from data.dataset.settings import MAX_SAMPLE_COUNT, MIN_SAMPLE_COUNT
from data.knowledge_base.models import NormalizedCVE

_ANNOTATOR = BIOAnnotator()


def make_kb_record(index: int = 0) -> NormalizedCVE:
    """Minimal CVE record with enough variety for template generation."""

    return NormalizedCVE(
        cve_id=f"CVE-2021-{10000 + index:05d}",
        description=f"Test vulnerability description {index}",
        cvss_score=7.5,
        severity="HIGH",
        products=["Apache", "OpenSSL", "nginx"],
        versions=["1.2.3", "2.4.1", "3.0.0"],
    )


def make_kb_records(count: int = 5) -> list[NormalizedCVE]:
    return [make_kb_record(index) for index in range(count)]


def make_annotated_sample(
    text: str,
    intent: str,
    *entities: tuple[str, str],
) -> DatasetSample:
    """Build a sample whose spans and BIO tags are internally consistent."""

    entity_values = [EntityValue(entity_type, value) for entity_type, value in entities]
    annotation = _ANNOTATOR.annotate(text, entity_values)
    return DatasetSample(
        text=text,
        intent=intent,
        entities=annotation.entities,
        tokens=annotation.tokens,
    )


def make_plain_sample(index: int) -> DatasetSample:
    """Lightweight sample for size/ratio checks (no entity spans)."""

    text = f"Sample query {index}"
    return DatasetSample(
        text=text,
        intent=INTENTS[index % len(INTENTS)],
        entities=[],
        tokens=[TokenAnnotation(token=text, tag="O", start=0, end=len(text))],
    )


def make_plain_samples(count: int) -> list[DatasetSample]:
    return [make_plain_sample(index) for index in range(count)]


def make_balanced_splits(total: int) -> dict[str, list[DatasetSample]]:
    """Split samples into train/validation/test with 70/15/15 proportions."""

    samples = make_plain_samples(total)
    train_count = round(total * 0.70)
    validation_count = round(total * 0.15)
    return {
        "train": samples[:train_count],
        "validation": samples[train_count : train_count + validation_count],
        "test": samples[train_count + validation_count :],
    }


def cve_lookup_sample() -> DatasetSample:
    return make_annotated_sample(
        "What is CVE-2021-44228?",
        "CVE_LOOKUP",
        ("CVE_ID", "CVE-2021-44228"),
    )


def sample_with_entity(entity_type: str, value: str, text: str | None = None) -> DatasetSample:
    """Helper for validator failure cases that need one controlled entity."""

    resolved_text = text or f"Check {value} details"
    return make_annotated_sample(resolved_text, "CVE_LOOKUP", (entity_type, value))
