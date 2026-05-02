"""Write generated datasets to disk."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from data.dataset.models import DatasetSample


class DatasetWriter:
    """Persist intent and NER datasets in the required output directory."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    @property
    def intents_path(self) -> Path:
        return self._output_dir / "intents.json"

    @property
    def ner_path(self) -> Path:
        return self._output_dir / "ner.conll"

    def write(self, splits: dict[str, list[DatasetSample]]) -> None:
        # Create the output directory once, then write both dataset views.
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self.write_intents(splits)
        self.write_ner(splits)

    def write_intents(self, splits: dict[str, list[DatasetSample]]) -> None:
        # Keep metadata beside data so downstream training can verify provenance quickly.
        payload = {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_samples": sum(len(samples) for samples in splits.values()),
                "splits": {name: len(samples) for name, samples in splits.items()},
                "intent_distribution": self._intent_distribution(splits),
            },
            "splits": {
                name: [sample.to_intent_record() for sample in samples]
                for name, samples in splits.items()
            },
        }
        with self.intents_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, ensure_ascii=False)
            file.write("\n")

    def write_ner(self, splits: dict[str, list[DatasetSample]]) -> None:
        with self.ner_path.open("w", encoding="utf-8") as file:
            for split_name in ("train", "validation", "test"):
                # Comments preserve split and intent context while staying CoNLL-compatible.
                file.write(f"# split = {split_name}\n")
                for sample in splits[split_name]:
                    file.write(f"# intent = {sample.intent}\n")
                    file.write(f"# text = {sample.text}\n")
                    for token in sample.tokens:
                        file.write(f"{token.token} {token.tag}\n")
                    file.write("\n")

    @staticmethod
    def _intent_distribution(splits: dict[str, list[DatasetSample]]) -> dict[str, dict[str, int]]:
        distribution: dict[str, dict[str, int]] = {}
        for split_name, samples in splits.items():
            counts = Counter(sample.intent for sample in samples)
            distribution[split_name] = dict(sorted(counts.items()))
        return distribution
