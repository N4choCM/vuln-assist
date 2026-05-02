"""Validation for generated intent and NER datasets."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from data.dataset.labels import ENTITY_TYPES, INTENTS
from data.dataset.models import DatasetSample, TokenAnnotation


@dataclass(frozen=True)
class ValidationReport:
    """Validation result for generated datasets."""

    errors: list[str]
    warnings: list[str]

    @property
    def is_valid(self) -> bool:
        return not self.errors


class DatasetValidator:
    """Validate coverage, splits, entity spans, and BIO consistency."""

    def validate(self, splits: dict[str, list[DatasetSample]]) -> ValidationReport:
        errors: list[str] = []
        warnings: list[str] = []
        # Flatten splits once so cross-dataset checks share the same sample view.
        samples = [sample for split_samples in splits.values() for sample in split_samples]

        self._validate_size(samples, errors)
        self._validate_intents(samples, errors, warnings)
        self._validate_splits(splits, errors)
        self._validate_samples(samples, errors)
        return ValidationReport(errors=errors, warnings=warnings)

    def raise_for_errors(self, report: ValidationReport) -> None:
        if report.errors:
            # Raise a single readable error instead of making callers inspect the report.
            joined_errors = "\n".join(f"- {error}" for error in report.errors)
            raise ValueError(f"Dataset validation failed:\n{joined_errors}")

    def _validate_size(self, samples: list[DatasetSample], errors: list[str]) -> None:
        if not 100 <= len(samples) <= 150:
            errors.append(f"Dataset size must be 100-150 samples, got {len(samples)}")

    def _validate_intents(
        self,
        samples: list[DatasetSample],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        counts = Counter(sample.intent for sample in samples)
        # Every project intent must appear at least once in the full dataset.
        missing = [intent for intent in INTENTS if counts[intent] == 0]
        if missing:
            errors.append(f"Missing intent coverage: {', '.join(missing)}")

        unknown = sorted(set(counts) - set(INTENTS))
        if unknown:
            errors.append(f"Unknown intents found: {', '.join(unknown)}")

        if counts:
            min_count = min(counts[intent] for intent in INTENTS)
            max_count = max(counts[intent] for intent in INTENTS)
            if max_count - min_count > 1:
                warnings.append(f"Intent distribution is not perfectly balanced: {dict(counts)}")

    def _validate_splits(
        self,
        splits: dict[str, list[DatasetSample]],
        errors: list[str],
    ) -> None:
        expected_splits = {"train", "validation", "test"}
        if set(splits) != expected_splits:
            errors.append("Splits must be train, validation, and test")
            return

        seen: dict[str, str] = {}
        for split_name, split_samples in splits.items():
            for sample in split_samples:
                # Lowercase text catches duplicate samples that differ only by casing.
                key = sample.text.lower()
                if key in seen:
                    errors.append(
                        f"Duplicate sample across splits: {sample.text!r} in "
                        f"{seen[key]} and {split_name}"
                    )
                seen[key] = split_name

        total = sum(len(split_samples) for split_samples in splits.values())
        if total == 0:
            errors.append("Cannot validate split ratios for an empty dataset")
            return

        ratios = {
            "train": len(splits["train"]) / total,
            "validation": len(splits["validation"]) / total,
            "test": len(splits["test"]) / total,
        }
        expected = {"train": 0.70, "validation": 0.15, "test": 0.15}
        for split_name, expected_ratio in expected.items():
            # Allow small rounding differences for sample counts not divisible by 20.
            if abs(ratios[split_name] - expected_ratio) > 0.03:
                errors.append(
                    f"{split_name} split ratio should be close to {expected_ratio:.2f}, "
                    f"got {ratios[split_name]:.2f}"
                )

    def _validate_samples(self, samples: list[DatasetSample], errors: list[str]) -> None:
        for sample in samples:
            if not sample.text.strip():
                errors.append("Empty text found")
            if "{" in sample.text or "}" in sample.text:
                errors.append(f"Unresolved placeholder in sample: {sample.text}")
            if re.search(r"\s{2,}", sample.text):
                errors.append(f"Repeated whitespace in sample: {sample.text}")
            self._validate_entities(sample, errors)
            self._validate_bio(sample.tokens, errors)

    def _validate_entities(self, sample: DatasetSample, errors: list[str]) -> None:
        for entity in sample.entities:
            if entity.entity_type not in ENTITY_TYPES:
                errors.append(f"Unknown entity type {entity.entity_type} in {sample.text}")
            # Character offsets must reproduce the exact text stored in the entity.
            if sample.text[entity.start : entity.end] != entity.value:
                errors.append(f"Entity span mismatch in {sample.text}: {entity}")
            # Every entity span must contain a B- tag to be trainable as BIO data.
            if not any(
                token.tag == f"B-{entity.entity_type}"
                and token.start >= entity.start
                and token.end <= entity.end
                for token in sample.tokens
            ):
                errors.append(f"Entity missing BIO beginning tag in {sample.text}: {entity}")

    def _validate_bio(self, tokens: list[TokenAnnotation], errors: list[str]) -> None:
        previous_entity_type = ""
        for token in tokens:
            if token.tag == "O":
                # Outside tokens reset the active entity chain.
                previous_entity_type = ""
                continue
            if "-" not in token.tag:
                errors.append(f"Invalid BIO tag: {token.tag}")
                previous_entity_type = ""
                continue
            prefix, entity_type = token.tag.split("-", 1)
            if prefix not in {"B", "I"}:
                errors.append(f"Invalid BIO prefix: {token.tag}")
            if entity_type not in ENTITY_TYPES:
                errors.append(f"Unknown BIO entity type: {token.tag}")
            if prefix == "I" and previous_entity_type != entity_type:
                # I-tags cannot start an entity or switch entity type without a B-tag.
                errors.append(f"I-tag without preceding entity: {token.token}/{token.tag}")
            previous_entity_type = entity_type
