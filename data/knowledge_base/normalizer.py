"""Normalize raw NVD CVE records into the project knowledge-base schema."""

from __future__ import annotations

import re
from typing import Any, Iterable, Mapping, Optional

from data.knowledge_base.models import NormalizedCVE


_UNKNOWN_CPE_VALUES = {"", "*", "-", "na", "n/a"}


class NVDRecordNormalizer:
    """Convert NVD API CVE records into normalized CVE objects."""

    def normalize_many(self, records: Iterable[Mapping[str, Any]]) -> list[NormalizedCVE]:
        """Normalize multiple NVD records, skipping malformed entries."""

        normalized: list[NormalizedCVE] = []
        seen_ids: set[str] = set()
        for record in records:
            cve = self.normalize_record(record)
            # Drop malformed records and duplicate CVE IDs before persisting the KB.
            if cve is None or cve.cve_id in seen_ids:
                continue
            normalized.append(cve)
            seen_ids.add(cve.cve_id)
        return normalized

    def normalize_record(self, record: Mapping[str, Any]) -> Optional[NormalizedCVE]:
        """Normalize one raw NVD vulnerability entry."""

        # NVD API responses wrap the CVE payload under "cve"; tests may pass it directly.
        cve = record.get("cve", record)
        if not isinstance(cve, Mapping):
            return None

        cve_id = str(cve.get("id", "")).strip().upper()
        if not cve_id:
            return None

        description = self._extract_description(cve)
        cvss_score, severity = self._extract_cvss(cve)
        products, versions = self._extract_affected_entities(cve)

        return NormalizedCVE(
            cve_id=cve_id,
            description=description,
            cvss_score=cvss_score,
            severity=severity,
            products=products,
            versions=versions,
        )

    def _extract_description(self, cve: Mapping[str, Any]) -> str:
        descriptions = cve.get("descriptions", [])
        if isinstance(descriptions, list):
            # Prefer English because the generated dataset is currently English.
            for item in descriptions:
                if isinstance(item, Mapping) and item.get("lang") == "en":
                    return str(item.get("value", "")).strip()
            # Fall back to any available description instead of losing the record.
            for item in descriptions:
                if isinstance(item, Mapping) and item.get("value"):
                    return str(item.get("value", "")).strip()
        return ""

    def _extract_cvss(self, cve: Mapping[str, Any]) -> tuple[float, str]:
        metrics = cve.get("metrics", {})
        if not isinstance(metrics, Mapping):
            return 0.0, "UNKNOWN"

        # Try the newest CVSS schema first, then fall back for older CVE records.
        metric_keys = ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2")
        for key in metric_keys:
            entries = metrics.get(key, [])
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, Mapping):
                    continue
                cvss_data = entry.get("cvssData", {})
                if not isinstance(cvss_data, Mapping):
                    continue
                score = self._read_float(cvss_data.get("baseScore"))
                if score is None:
                    continue
                # Some NVD metric versions store severity beside cvssData instead of inside it.
                severity = str(
                    cvss_data.get("baseSeverity") or entry.get("baseSeverity") or ""
                ).strip()
                return score, (severity.upper() if severity else self._severity_from_score(score))

        return 0.0, "UNKNOWN"

    def _extract_affected_entities(self, cve: Mapping[str, Any]) -> tuple[list[str], list[str]]:
        products: list[str] = []
        versions: list[str] = []

        configurations = cve.get("configurations", [])
        if not isinstance(configurations, list):
            return products, versions

        for configuration in configurations:
            if not isinstance(configuration, Mapping):
                continue
            # NVD configurations can be nested, so walk every node recursively.
            for node in self._walk_nodes(configuration):
                cpe_matches = node.get("cpeMatch", [])
                if not isinstance(cpe_matches, list):
                    continue
                for match in cpe_matches:
                    # Non-vulnerable CPE matches are context, not affected products.
                    if not isinstance(match, Mapping) or match.get("vulnerable") is False:
                        continue
                    parsed = self._parse_cpe_23(str(match.get("criteria", "")))
                    if parsed.product:
                        products.append(parsed.product)
                    versions.extend(self._versions_from_match(parsed.version, match))

        return self._unique(products), self._unique(versions)

    def _walk_nodes(self, node: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
        yield node
        children = node.get("nodes", [])
        if isinstance(children, list):
            for child in children:
                if isinstance(child, Mapping):
                    yield from self._walk_nodes(child)

    def _versions_from_match(self, cpe_version: str, match: Mapping[str, Any]) -> list[str]:
        versions: list[str] = []
        # Direct CPE versions are preferred when they are concrete values.
        if cpe_version and cpe_version.lower() not in _UNKNOWN_CPE_VALUES:
            versions.append(cpe_version)

        # NVD may encode affected ranges separately from the CPE version field.
        range_parts = []
        range_keys = (
            ("versionStartIncluding", ">="),
            ("versionStartExcluding", ">"),
            ("versionEndIncluding", "<="),
            ("versionEndExcluding", "<"),
        )
        for key, operator in range_keys:
            value = str(match.get(key, "")).strip()
            if value:
                range_parts.append(f"{operator} {value}")
        if range_parts:
            versions.append(", ".join(range_parts))
        return versions

    def _parse_cpe_23(self, criteria: str) -> "_ParsedCPE":
        parts = self._split_cpe(criteria)
        if len(parts) < 6 or parts[0] != "cpe" or parts[1] != "2.3":
            return _ParsedCPE(product="", version="")

        # CPE 2.3 positions: part, vendor, product, version after the cpe:2.3 prefix.
        vendor = self._clean_cpe_component(parts[3])
        product = self._clean_cpe_component(parts[4])
        version = self._clean_cpe_component(parts[5])
        if not product or product.lower() in _UNKNOWN_CPE_VALUES:
            return _ParsedCPE(product="", version=version)

        product_name = product
        # Prefix the vendor when it adds useful context and is not already in the product name.
        if vendor and vendor.lower() not in _UNKNOWN_CPE_VALUES and vendor.lower() not in product.lower():
            product_name = f"{vendor} {product}"
        return _ParsedCPE(product=product_name, version=version)

    def _split_cpe(self, criteria: str) -> list[str]:
        parts: list[str] = []
        current: list[str] = []
        escaped = False
        for char in criteria:
            if escaped:
                # Escaped separators belong to the current CPE component.
                current.append(char)
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == ":":
                parts.append("".join(current))
                current = []
            else:
                current.append(char)
        parts.append("".join(current))
        return parts

    def _clean_cpe_component(self, value: str) -> str:
        # CPE components use underscores and escapes; dataset entities should be readable text.
        cleaned = value.replace("\\", "").replace("_", " ").strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    @staticmethod
    def _read_float(value: object) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _severity_from_score(score: float) -> str:
        # CVSS qualitative ratings follow the common v3/v4 score bands.
        if score <= 0:
            return "NONE"
        if score < 4.0:
            return "LOW"
        if score < 7.0:
            return "MEDIUM"
        if score < 9.0:
            return "HIGH"
        return "CRITICAL"

    @staticmethod
    def _unique(values: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        unique_values: list[str] = []
        for value in values:
            normalized = re.sub(r"\s+", " ", value).strip()
            key = normalized.lower()
            # Preserve first-seen casing while deduplicating case-insensitively.
            if normalized and key not in seen:
                unique_values.append(normalized)
                seen.add(key)
        return unique_values


class _ParsedCPE:
    def __init__(self, product: str, version: str) -> None:
        self.product = product
        self.version = version
