"""Entity sampling from normalized CVE knowledge-base records."""

from __future__ import annotations

import random
from typing import Iterable

from data.dataset.labels import METRICS, SEVERITIES
from data.dataset.models import EntityValue
from data.knowledge_base.models import NormalizedCVE


class EntitySampler:
    """Sample real-world entities from the normalized knowledge base."""

    def __init__(self, records: Iterable[NormalizedCVE], rng: random.Random) -> None:
        # Keep only records that can provide a CVE_ID entity.
        self._records = [record for record in records if record.cve_id]
        if not self._records:
            raise ValueError("EntitySampler requires at least one normalized CVE record")
        self._rng = rng
        # Precompute fallback pools once so sampling stays simple and deterministic.
        self._severities = self._build_severities()
        self._products = self._build_values("products")
        self._versions = self._build_values("versions")

    def sample_values(self, placeholders: tuple[str, ...]) -> dict[str, str]:
        """Sample values for a template's placeholders."""

        # A single anchor record keeps related CVE/product/version values coherent.
        record = self._rng.choice(self._records)
        values: dict[str, str] = {}
        for placeholder in placeholders:
            if placeholder == "CVE_ID":
                values[placeholder] = record.cve_id
            elif placeholder == "PRODUCT":
                values[placeholder] = self._sample_product(record)
            elif placeholder == "VERSION":
                values[placeholder] = self._sample_version(record)
            elif placeholder == "SEVERITY":
                values[placeholder] = self._sample_severity(record)
            elif placeholder == "METRIC":
                values[placeholder] = self._rng.choice(METRICS)
            else:
                raise ValueError(f"Unsupported placeholder: {placeholder}")
        return values

    def entity_values(self, values: dict[str, str]) -> list[EntityValue]:
        """Convert injected values to entity descriptors for annotation."""

        seen: set[tuple[str, str]] = set()
        entities: list[EntityValue] = []
        for entity_type, value in values.items():
            # Deduplicate by type and case-insensitive value for clean BIO annotation.
            key = (entity_type, value.lower())
            if key in seen:
                continue
            entities.append(EntityValue(entity_type=entity_type, value=value))
            seen.add(key)
        return entities

    def _sample_product(self, record: NormalizedCVE) -> str:
        # Prefer products from the selected CVE, then fall back to the global KB pool.
        if record.products:
            return self._rng.choice(record.products)
        return self._rng.choice(self._products)

    def _sample_version(self, record: NormalizedCVE) -> str:
        # Prefer versions from the selected CVE, then fall back to the global KB pool.
        if record.versions:
            return self._rng.choice(record.versions)
        return self._rng.choice(self._versions)

    def _sample_severity(self, record: NormalizedCVE) -> str:
        severity = record.severity.strip().lower()
        # Unknown severities are not useful entities, so replace them with a known label.
        if severity and severity != "unknown":
            return severity
        return self._rng.choice(self._severities)

    def _build_severities(self) -> tuple[str, ...]:
        # Use real KB severities when available; otherwise use the project fallback labels.
        values = {
            record.severity.strip().lower()
            for record in self._records
            if record.severity and record.severity.strip().lower() != "unknown"
        }
        return tuple(sorted(values or set(SEVERITIES)))

    def _build_values(self, attribute: str) -> tuple[str, ...]:
        # Keep output order/casing in values while using seen for case-insensitive dedupe.
        values: list[str] = []
        seen: set[str] = set()
        for record in self._records:
            for value in getattr(record, attribute):
                normalized = value.strip()
                key = normalized.lower()
                if normalized and key not in seen:
                    values.append(normalized)
                    seen.add(key)
        if not values:
            raise ValueError(f"Knowledge base does not contain {attribute}")
        return tuple(values)
