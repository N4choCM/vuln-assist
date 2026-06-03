"""Unit tests for ``data.dataset.pipeline.builder.DatasetBuilder``."""

from __future__ import annotations

import pytest

from data.dataset.labels import INTENTS
from data.dataset.pipeline import DatasetBuilder, DatasetSplitter, DatasetValidator
from data.dataset.settings import MAX_SAMPLE_COUNT, MIN_SAMPLE_COUNT
from tests.dataset_pipeline_fixtures import make_kb_records


def test_build_rejects_sample_count_below_minimum() -> None:
    with pytest.raises(ValueError, match=str(MIN_SAMPLE_COUNT)):
        DatasetBuilder(make_kb_records(), sample_count=MIN_SAMPLE_COUNT - 1)


def test_build_rejects_sample_count_above_maximum() -> None:
    with pytest.raises(ValueError, match=str(MAX_SAMPLE_COUNT)):
        DatasetBuilder(make_kb_records(), sample_count=MAX_SAMPLE_COUNT + 1)


def test_build_returns_requested_sample_count() -> None:
    samples = DatasetBuilder(make_kb_records(), sample_count=MIN_SAMPLE_COUNT, seed=7).build()

    assert len(samples) == MIN_SAMPLE_COUNT


def test_build_covers_all_intents_with_balanced_distribution() -> None:
    samples = DatasetBuilder(make_kb_records(), sample_count=MIN_SAMPLE_COUNT, seed=7).build()
    counts = {intent: 0 for intent in INTENTS}

    for sample in samples:
        counts[sample.intent] += 1

    assert all(count > 0 for count in counts.values())
    assert max(counts.values()) - min(counts.values()) <= 1


def test_build_produces_unique_texts() -> None:
    samples = DatasetBuilder(make_kb_records(), sample_count=MIN_SAMPLE_COUNT, seed=7).build()
    normalized_texts = [sample.text.lower() for sample in samples]

    assert len(normalized_texts) == len(set(normalized_texts))


def test_build_samples_include_required_entity_spans() -> None:
    samples = DatasetBuilder(make_kb_records(), sample_count=MIN_SAMPLE_COUNT, seed=7).build()

    for sample in samples:
        if sample.intent == "GENERAL_QUERY":
            continue
        assert sample.entities, f"Expected entities in sample: {sample.text!r}"
        assert any(token.tag != "O" for token in sample.tokens)
        assert "{" not in sample.text and "}" not in sample.text


def test_build_output_passes_validator_after_split() -> None:
    samples = DatasetBuilder(make_kb_records(), sample_count=MIN_SAMPLE_COUNT, seed=7).build()
    splits = DatasetSplitter(seed=7).split(samples)
    report = DatasetValidator().validate(splits)

    assert report.is_valid, report.errors
