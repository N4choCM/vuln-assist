"""Train, validation, and test splitting for generated samples."""

from __future__ import annotations

import math
import random
from collections import defaultdict

from data.dataset.labels import INTENTS
from data.dataset.models import DatasetSample


class DatasetSplitter:
    """Create balanced 70/15/15 train, validation, and test splits."""

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)

    def split(self, samples: list[DatasetSample]) -> dict[str, list[DatasetSample]]:
        by_intent: dict[str, list[DatasetSample]] = defaultdict(list)
        for sample in samples:
            by_intent[sample.intent].append(sample)

        # Compute global split targets first, then allocate each target by intent.
        total = len(samples)
        target_train = round(total * 0.70)
        target_validation = round(total * 0.15)
        train_counts = self._allocate_by_intent(by_intent, target_train)
        # Validation allocation runs over samples left after assigning train rows.
        remaining_after_train = {
            intent: len(by_intent[intent]) - train_counts[intent]
            for intent in INTENTS
        }
        validation_counts = self._allocate_counts(remaining_after_train, target_validation)

        splits = {"train": [], "validation": [], "test": []}
        for intent in INTENTS:
            intent_samples = list(by_intent[intent])
            # Shuffle within each intent before slicing so each split gets variety.
            self._rng.shuffle(intent_samples)
            train_count = train_counts[intent]
            validation_count = validation_counts[intent]
            splits["train"].extend(intent_samples[:train_count])
            splits["validation"].extend(
                intent_samples[train_count : train_count + validation_count]
            )
            splits["test"].extend(intent_samples[train_count + validation_count :])

        for split_samples in splits.values():
            # Shuffle final splits to avoid intent-grouped output files.
            self._rng.shuffle(split_samples)
        return splits

    def _allocate_by_intent(
        self,
        by_intent: dict[str, list[DatasetSample]],
        target_total: int,
    ) -> dict[str, int]:
        counts = {intent: len(by_intent[intent]) for intent in INTENTS}
        return self._allocate_counts(counts, target_total)

    @staticmethod
    def _allocate_counts(counts: dict[str, int], target_total: int) -> dict[str, int]:
        total = sum(counts.values())
        if total == 0:
            return {intent: 0 for intent in INTENTS}

        allocations: dict[str, int] = {}
        remainders: list[tuple[float, str]] = []
        for intent in INTENTS:
            # Floor the exact proportional count, then distribute leftover rows below.
            exact = counts[intent] * target_total / total
            allocated = min(counts[intent], math.floor(exact))
            allocations[intent] = allocated
            remainders.append((exact - allocated, intent))

        remaining = target_total - sum(allocations.values())
        for _, intent in sorted(remainders, reverse=True):
            if remaining <= 0:
                break
            if allocations[intent] >= counts[intent]:
                continue
            # Largest-remainder allocation keeps the final total exactly on target.
            allocations[intent] += 1
            remaining -= 1

        return allocations
