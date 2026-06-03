"""Unit tests for ``data.dataset.pipeline.writer.DatasetWriter``."""

from __future__ import annotations

import json

from data.dataset.pipeline import DatasetWriter
from tests.dataset_pipeline_fixtures import cve_lookup_sample, make_balanced_splits


def test_write_creates_intents_json_and_ner_conll(tmp_path) -> None:
    splits = make_balanced_splits(100)
    writer = DatasetWriter(tmp_path)

    writer.write(splits)

    assert writer.intents_path.is_file()
    assert writer.ner_path.is_file()


def test_intents_json_contains_metadata_and_split_records(tmp_path) -> None:
    sample = cve_lookup_sample()
    splits = {
        "train": [sample],
        "validation": [],
        "test": [],
    }
    writer = DatasetWriter(tmp_path)
    writer.write_intents(splits)

    payload = json.loads(writer.intents_path.read_text(encoding="utf-8"))

    assert payload["metadata"]["total_samples"] == 1
    assert payload["metadata"]["splits"] == {"train": 1, "validation": 0, "test": 0}
    assert payload["splits"]["train"][0]["text"] == sample.text
    assert payload["splits"]["train"][0]["intent"] == sample.intent
    assert payload["splits"]["train"][0]["entities"][0]["type"] == "CVE_ID"


def test_ner_conll_contains_split_markers_and_bio_lines(tmp_path) -> None:
    sample = cve_lookup_sample()
    splits = {"train": [sample], "validation": [], "test": []}
    writer = DatasetWriter(tmp_path)
    writer.write_ner(splits)

    content = writer.ner_path.read_text(encoding="utf-8")

    assert "# split = train" in content
    assert f"# intent = {sample.intent}" in content
    assert f"# text = {sample.text}" in content
    assert any(line.endswith(" B-CVE_ID") for line in content.splitlines())


def test_write_creates_output_directory_when_missing(tmp_path) -> None:
    output_dir = tmp_path / "nested" / "output"
    writer = DatasetWriter(output_dir)

    writer.write(make_balanced_splits(100))

    assert output_dir.is_dir()
