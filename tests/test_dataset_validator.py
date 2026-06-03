"""Unit tests for ``data.dataset.pipeline.validator.DatasetValidator``."""

from __future__ import annotations

import pytest

from data.dataset.labels import INTENTS
from data.dataset.models import DatasetSample, EntitySpan, TokenAnnotation
from data.dataset.pipeline import DatasetValidator
from data.dataset.settings import MAX_SAMPLE_COUNT, MIN_SAMPLE_COUNT
from tests.dataset_pipeline_fixtures import (
    cve_lookup_sample,
    make_balanced_splits,
    make_plain_samples,
    sample_with_entity,
)


def test_validator_accepts_valid_balanced_splits() -> None:
    report = DatasetValidator().validate(make_balanced_splits(MIN_SAMPLE_COUNT))

    assert report.is_valid
    assert not report.errors


def test_validator_accepts_configured_maximum_dataset_size() -> None:
    report = DatasetValidator().validate(make_balanced_splits(MAX_SAMPLE_COUNT))

    assert report.is_valid


def test_validator_rejects_dataset_size_below_minimum() -> None:
    report = DatasetValidator().validate(make_balanced_splits(MIN_SAMPLE_COUNT - 1))

    assert not report.is_valid
    assert any(str(MIN_SAMPLE_COUNT) in error for error in report.errors)


def test_validator_rejects_dataset_size_above_maximum() -> None:
    report = DatasetValidator().validate(make_balanced_splits(MAX_SAMPLE_COUNT + 1))

    assert not report.is_valid
    assert any("100-1000 samples" in error for error in report.errors)


def test_validator_rejects_missing_intent_coverage() -> None:
    samples = [
        DatasetSample(
            text=f"Sample {index}",
            intent="CVE_LOOKUP",
            entities=[],
            tokens=[TokenAnnotation(token=f"Sample {index}", tag="O", start=0, end=8)],
        )
        for index in range(MIN_SAMPLE_COUNT)
    ]
    train_count = round(MIN_SAMPLE_COUNT * 0.70)
    validation_count = round(MIN_SAMPLE_COUNT * 0.15)
    splits = {
        "train": samples[:train_count],
        "validation": samples[train_count : train_count + validation_count],
        "test": samples[train_count + validation_count :],
    }

    report = DatasetValidator().validate(splits)

    assert not report.is_valid
    assert any("Missing intent coverage" in error for error in report.errors)


def test_validator_rejects_unknown_intent() -> None:
    splits = make_balanced_splits(MIN_SAMPLE_COUNT)
    splits["train"][0] = DatasetSample(
        text="Unknown intent sample",
        intent="NOT_A_REAL_INTENT",
        entities=[],
        tokens=[TokenAnnotation(token="Unknown", tag="O", start=0, end=7)],
    )

    report = DatasetValidator().validate(splits)

    assert not report.is_valid
    assert any("Unknown intents found" in error for error in report.errors)


def test_validator_warns_on_unbalanced_intent_distribution() -> None:
    samples = [
        DatasetSample(
            text=f"Sample {index}",
            intent="CVE_LOOKUP",
            entities=[],
            tokens=[TokenAnnotation(token=f"Sample {index}", tag="O", start=0, end=8)],
        )
        for index in range(MIN_SAMPLE_COUNT - len(INTENTS) + 1)
    ]
    for intent in INTENTS[1:]:
        text = f"Single {intent} sample"
        samples.append(
            DatasetSample(
                text=text,
                intent=intent,
                entities=[],
                tokens=[TokenAnnotation(token="Single", tag="O", start=0, end=6)],
            )
        )
    train_count = round(len(samples) * 0.70)
    validation_count = round(len(samples) * 0.15)
    splits = {
        "train": samples[:train_count],
        "validation": samples[train_count : train_count + validation_count],
        "test": samples[train_count + validation_count :],
    }

    report = DatasetValidator().validate(splits)

    assert any("not perfectly balanced" in warning for warning in report.warnings)


def test_validator_rejects_invalid_split_keys() -> None:
    report = DatasetValidator().validate({"train": [], "dev": [], "holdout": []})

    assert not report.is_valid
    assert any("Splits must be train, validation, and test" in error for error in report.errors)


def test_validator_rejects_duplicate_sample_across_splits() -> None:
    duplicate = cve_lookup_sample()
    splits = make_balanced_splits(MIN_SAMPLE_COUNT)
    splits["validation"] = [duplicate]
    splits["test"] = [duplicate]

    report = DatasetValidator().validate(splits)

    assert not report.is_valid
    assert any("Duplicate sample across splits" in error for error in report.errors)


def test_validator_rejects_invalid_split_ratios() -> None:
    samples = make_plain_samples(MIN_SAMPLE_COUNT)
    splits = {
        "train": samples[:50],
        "validation": samples[50:75],
        "test": samples[75:],
    }

    report = DatasetValidator().validate(splits)

    assert not report.is_valid
    assert any("split ratio should be close to" in error for error in report.errors)


def test_validator_rejects_empty_text() -> None:
    splits = make_balanced_splits(MIN_SAMPLE_COUNT)
    splits["train"][0] = DatasetSample(
        text="   ",
        intent="GENERAL_QUERY",
        entities=[],
        tokens=[],
    )

    report = DatasetValidator().validate(splits)

    assert not report.is_valid
    assert any("Empty text found" in error for error in report.errors)


def test_validator_rejects_unresolved_placeholder() -> None:
    splits = make_balanced_splits(MIN_SAMPLE_COUNT)
    splits["train"][0] = DatasetSample(
        text="What is {CVE_ID}?",
        intent="CVE_LOOKUP",
        entities=[],
        tokens=[TokenAnnotation(token="What", tag="O", start=0, end=4)],
    )

    report = DatasetValidator().validate(splits)

    assert not report.is_valid
    assert any("Unresolved placeholder" in error for error in report.errors)


def test_validator_rejects_repeated_whitespace() -> None:
    splits = make_balanced_splits(MIN_SAMPLE_COUNT)
    splits["train"][0] = DatasetSample(
        text="What  is  CVE-2021-44228?",
        intent="CVE_LOOKUP",
        entities=[],
        tokens=[TokenAnnotation(token="What", tag="O", start=0, end=4)],
    )

    report = DatasetValidator().validate(splits)

    assert not report.is_valid
    assert any("Repeated whitespace" in error for error in report.errors)


def test_validator_rejects_unknown_entity_type() -> None:
    sample = sample_with_entity("CVE_ID", "CVE-2021-44228")
    bad_entity = EntitySpan("VENDOR", "Apache", 0, 6)
    splits = make_balanced_splits(MIN_SAMPLE_COUNT)
    splits["train"][0] = DatasetSample(
        text=sample.text,
        intent=sample.intent,
        entities=[bad_entity],
        tokens=sample.tokens,
    )

    report = DatasetValidator().validate(splits)

    assert not report.is_valid
    assert any("Unknown entity type" in error for error in report.errors)


def test_validator_rejects_entity_span_mismatch() -> None:
    sample = cve_lookup_sample()
    bad_entity = EntitySpan("CVE_ID", "CVE-9999-9999", sample.entities[0].start, sample.entities[0].end)
    splits = make_balanced_splits(MIN_SAMPLE_COUNT)
    splits["train"][0] = DatasetSample(
        text=sample.text,
        intent=sample.intent,
        entities=[bad_entity],
        tokens=sample.tokens,
    )

    report = DatasetValidator().validate(splits)

    assert not report.is_valid
    assert any("Entity span mismatch" in error for error in report.errors)


def test_validator_rejects_entity_missing_bio_begin_tag() -> None:
    sample = cve_lookup_sample()
    tokens_without_b = [
        TokenAnnotation(token=token.token, tag="O", start=token.start, end=token.end)
        for token in sample.tokens
    ]
    splits = make_balanced_splits(MIN_SAMPLE_COUNT)
    splits["train"][0] = DatasetSample(
        text=sample.text,
        intent=sample.intent,
        entities=sample.entities,
        tokens=tokens_without_b,
    )

    report = DatasetValidator().validate(splits)

    assert not report.is_valid
    assert any("Entity missing BIO beginning tag" in error for error in report.errors)


def test_validator_rejects_invalid_bio_tag() -> None:
    splits = make_balanced_splits(MIN_SAMPLE_COUNT)
    splits["train"][0] = DatasetSample(
        text="bad bio",
        intent="GENERAL_QUERY",
        entities=[],
        tokens=[TokenAnnotation(token="bad", tag="X-CVE_ID", start=0, end=3)],
    )

    report = DatasetValidator().validate(splits)

    assert not report.is_valid
    assert any("Invalid BIO prefix" in error for error in report.errors)


def test_validator_rejects_i_tag_without_preceding_entity() -> None:
    splits = make_balanced_splits(MIN_SAMPLE_COUNT)
    splits["train"][0] = DatasetSample(
        text="apache server",
        intent="PRODUCT_SEARCH",
        entities=[],
        tokens=[
            TokenAnnotation(token="apache", tag="I-PRODUCT", start=0, end=6),
            TokenAnnotation(token="server", tag="O", start=7, end=13),
        ],
    )

    report = DatasetValidator().validate(splits)

    assert not report.is_valid
    assert any("I-tag without preceding entity" in error for error in report.errors)


def test_raise_for_errors_raises_with_joined_messages() -> None:
    report = DatasetValidator().validate(make_balanced_splits(MIN_SAMPLE_COUNT - 1))

    with pytest.raises(ValueError, match="Dataset validation failed"):
        DatasetValidator().raise_for_errors(report)
