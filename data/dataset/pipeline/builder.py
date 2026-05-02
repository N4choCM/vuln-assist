"""Build generated NLU samples from templates and KB entities."""

from __future__ import annotations

import random
import re
from collections import Counter
from typing import Iterable

from data.dataset.bio_annotator import BIOAnnotator
from data.dataset.entity_sampler import EntitySampler
from data.dataset.labels import INTENTS
from data.dataset.models import DatasetSample
from data.dataset.paraphraser import RuleBasedParaphraser
from data.dataset.templates import TEMPLATES, QueryTemplate
from data.knowledge_base.models import NormalizedCVE


class DatasetBuilder:
    """Generate balanced intent and NER samples."""

    def __init__(
        self,
        records: Iterable[NormalizedCVE],
        sample_count: int = 120,
        seed: int = 42,
    ) -> None:
        if sample_count < 100 or sample_count > 150:
            raise ValueError("sample_count must be between 100 and 150")
        self._records = list(records)
        self._sample_count = sample_count
        # One seeded RNG is shared across sampling and paraphrasing for reproducibility.
        self._rng = random.Random(seed)
        self._sampler = EntitySampler(self._records, self._rng)
        self._paraphraser = RuleBasedParaphraser()
        self._annotator = BIOAnnotator()

    def build(self) -> list[DatasetSample]:
        """Generate unique, balanced samples."""

        targets = self._intent_targets()
        samples: list[DatasetSample] = []
        # Track generated text globally to avoid duplicates across all intents.
        seen_texts: set[str] = set()

        for intent in INTENTS:
            intent_samples = self._generate_for_intent(
                intent=intent,
                target_count=targets[intent],
                seen_texts=seen_texts,
            )
            samples.extend(intent_samples)

        self._rng.shuffle(samples)
        return samples

    def _generate_for_intent(
        self,
        intent: str,
        target_count: int,
        seen_texts: set[str],
    ) -> list[DatasetSample]:
        templates = TEMPLATES[intent]
        samples: list[DatasetSample] = []
        attempts = 0
        # Cap retries so a low-variety template set fails loudly instead of looping forever.
        max_attempts = target_count * 100

        while len(samples) < target_count and attempts < max_attempts:
            attempts += 1
            template = self._select_template(templates, attempts)
            # Paraphrase before rendering so placeholders remain easy to replace.
            template_text = self._paraphraser.paraphrase(template.text, self._rng)
            values = self._sampler.sample_values(template.placeholders)
            text = self._clean_text(QueryTemplate(intent, template_text).render(values))
            key = text.lower()
            if key in seen_texts:
                continue

            # Convert sampled placeholder values into spans and token-level BIO labels.
            entity_values = self._sampler.entity_values(values)
            annotation = self._annotator.annotate(text, entity_values)
            sample = DatasetSample(
                text=text,
                intent=intent,
                entities=annotation.entities,
                tokens=annotation.tokens,
            )
            if self._is_usable(sample, template.placeholders):
                samples.append(sample)
                seen_texts.add(key)

        if len(samples) < target_count:
            raise RuntimeError(
                f"Could only generate {len(samples)} samples for {intent}; "
                f"target was {target_count}"
            )
        return samples

    def _select_template(self, templates: tuple[QueryTemplate, ...], attempts: int) -> QueryTemplate:
        # Cycle through templates while still allowing entity and paraphrase variation.
        index = attempts % len(templates)
        return templates[index]

    def _intent_targets(self) -> dict[str, int]:
        # Distribute the requested sample count as evenly as possible across intents.
        base = self._sample_count // len(INTENTS)
        remainder = self._sample_count % len(INTENTS)
        return {
            intent: base + (1 if index < remainder else 0)
            for index, intent in enumerate(INTENTS)
        }

    def _is_usable(self, sample: DatasetSample, placeholders: tuple[str, ...]) -> bool:
        # Reject unresolved template variables before the sample reaches validation.
        if "{" in sample.text or "}" in sample.text:
            return False
        # Repeated whitespace usually indicates a broken replacement.
        if re.search(r"\s{2,}", sample.text):
            return False

        expected_counts = Counter(placeholders)
        for entity_type, expected_count in expected_counts.items():
            # Every placeholder should result in at least one annotated entity.
            actual_count = sum(1 for entity in sample.entities if entity.entity_type == entity_type)
            if actual_count < expected_count:
                return False
        return True

    @staticmethod
    def _clean_text(text: str) -> str:
        # Match the paraphraser cleanup for rendered text after entity injection.
        cleaned = re.sub(r"\s+", " ", text).strip()
        cleaned = cleaned.replace("?.", "?").replace("..", ".")
        return cleaned
