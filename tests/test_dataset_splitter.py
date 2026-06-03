"""Unit tests for ``data.dataset.pipeline.splitter.DatasetSplitter``."""

from __future__ import annotations

from data.dataset.labels import INTENTS
from data.dataset.pipeline import DatasetSplitter, DatasetValidator
from tests.dataset_pipeline_fixtures import make_plain_samples


def test_splitter_preserves_samples_and_ratios() -> None:
    samples = make_plain_samples(600)
    splits = DatasetSplitter(seed=7).split(samples)

    assert len(splits["train"]) + len(splits["validation"]) + len(splits["test"]) == 600
    assert abs(len(splits["train"]) / 600 - 0.70) <= 0.03
    assert abs(len(splits["validation"]) / 600 - 0.15) <= 0.03
    assert abs(len(splits["test"]) / 600 - 0.15) <= 0.03

    texts = [sample.text for split_samples in splits.values() for sample in split_samples]
    assert len(texts) == len(set(texts))

    report = DatasetValidator().validate(splits)
    assert report.is_valid


def test_splitter_is_reproducible_with_same_seed() -> None:
    samples = make_plain_samples(120)

    first = DatasetSplitter(seed=99).split(samples)
    second = DatasetSplitter(seed=99).split(samples)

    for split_name in ("train", "validation", "test"):
        assert [sample.text for sample in first[split_name]] == [
            sample.text for sample in second[split_name]
        ]


def test_splitter_empty_input_produces_empty_splits() -> None:
    splits = DatasetSplitter(seed=1).split([])

    assert set(splits) == {"train", "validation", "test"}
    assert all(len(split_samples) == 0 for split_samples in splits.values())


def test_allocate_proportionally_respects_available_counts() -> None:
    counts = {"CVE_LOOKUP": 40, "CVSS_QUERY": 20, **{intent: 0 for intent in INTENTS[2:]}}
    allocated = DatasetSplitter._allocate_proportionally(counts, 15)

    assert sum(allocated.values()) == 15
    assert allocated["CVE_LOOKUP"] == 10
    assert allocated["CVSS_QUERY"] == 5


def test_allocate_proportionally_returns_zeros_when_no_samples() -> None:
    counts = {intent: 0 for intent in INTENTS}
    allocated = DatasetSplitter._allocate_proportionally(counts, 10)

    assert allocated == {intent: 0 for intent in INTENTS}
