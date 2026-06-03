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
        samples_by_intent: dict[str, list[DatasetSample]] = defaultdict(list)
        for sample in samples:
            samples_by_intent[sample.intent].append(sample)

        # Compute global split targets first, then allocate each target by intent.
        total_samples = len(samples)
        target_train = round(total_samples * 0.70)
        target_validation = round(total_samples * 0.15)
        samples_count_by_intent = {
            intent: len(samples_by_intent[intent]) for intent in INTENTS
        }
        train_samples_counts_by_intent = self._allocate_proportionally(samples_count_by_intent, target_train)
        # Validation allocation runs over samples left after assigning train rows.
        remaining_samples_after_train_split = {
            intent: samples_count_by_intent[intent] - train_samples_counts_by_intent[intent]
            for intent in INTENTS
        }
        validation_samples_counts_by_intent = self._allocate_proportionally(remaining_samples_after_train_split, target_validation)

        splits = {"train": [], "validation": [], "test": []}
        for intent in INTENTS:
            intent_samples = list(samples_by_intent[intent])
            # Shuffle within each intent before slicing so each split gets variety.
            self._rng.shuffle(intent_samples)
            train_samples_count = train_samples_counts_by_intent[intent]
            validation_samples_count = validation_samples_counts_by_intent[intent]
            splits["train"].extend(intent_samples[:train_samples_count])
            splits["validation"].extend(intent_samples[train_samples_count : train_samples_count + validation_samples_count])
            splits["test"].extend(intent_samples[train_samples_count + validation_samples_count :])

        for split_samples in splits.values():
            # Shuffle final splits to avoid intent-grouped output files.
            self._rng.shuffle(split_samples)
        return splits

    @staticmethod
    def _allocate_proportionally(counts_per_intent: dict[str, int], target_total: int) -> dict[str, int]:
        """Split ``target_total`` across intents in proportion to ``counts_per_intent``."""

        total = sum(counts_per_intent.values())
        if total == 0:
            return {intent: 0 for intent in INTENTS}

        allocations: dict[str, int] = {}
        remainders: list[tuple[float, str]] = []
        for intent in INTENTS:
            # Floor the exact proportional count, then distribute leftover rows below.
            exact = counts_per_intent[intent] * target_total / total
            allocated = min(counts_per_intent[intent], math.floor(exact))
            allocations[intent] = allocated
            remainders.append((exact - allocated, intent))

        remaining = target_total - sum(allocations.values())
        for _, intent in sorted(remainders, reverse=True):
            if remaining <= 0:
                break
            if allocations[intent] >= counts_per_intent[intent]:
                continue
            # Largest-remainder allocation keeps the final total exactly on target.
            allocations[intent] += 1
            remaining -= 1

        return allocations
