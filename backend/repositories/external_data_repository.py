"""Orchestrate live NVD retrieval, normalization, and optional MITRE enrichment."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

from data.knowledge_base.models import NormalizedCVE
from data.knowledge_base.normalizer import NVDRecordNormalizer
from data.knowledge_base.repository import KnowledgeBaseRepository
from integrations.mitre.cache import MITREAttackCache
from integrations.nvd.client import NVDClient, NVDQuery

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KB_PATH = PROJECT_ROOT / "data" / "knowledge_base" / "cves.json"
DEFAULT_SEED_KB_PATH = PROJECT_ROOT / "data" / "knowledge_base" / "seed_cves.json"


class ExternalDataRepository:
    """Fetch vulnerability data for Phase 4 without embedding query-building rules."""

    def __init__(
        self,
        nvd_client: NVDClient | None = None,
        normalizer: NVDRecordNormalizer | None = None,
        knowledge_base: KnowledgeBaseRepository | None = None,
        mitre_cache: MITREAttackCache | None = None,
    ) -> None:
        self._nvd = nvd_client or NVDClient()
        self._normalizer = normalizer or NVDRecordNormalizer()
        self._kb = knowledge_base or KnowledgeBaseRepository(_resolve_kb_path())
        self._mitre = mitre_cache or MITREAttackCache.load_default()

    def fetch(
        self,
        intent: str,
        slots: dict[str, str],
        query: NVDQuery,
        limit: int,
    ) -> dict[str, object]:
        """Execute an NVD query and return a serializable retrieval payload."""

        errors: list[str] = []
        raw_records: list[dict[str, Any]] = []
        source = "nvd_live"

        try:
            raw_records = self._nvd.fetch_cves(query=query, total_limit=limit)
        except Exception as exc:  # noqa: BLE001 — surface integration failures to callers
            errors.append(str(exc))
            fallback = self._fallback_cve(slots)
            if fallback is not None:
                return self._build_result(
                    intent=intent,
                    cves=[fallback],
                    raw_records=[],
                    mitre_techniques=[],
                    source="knowledge_base_fallback",
                    errors=errors,
                )
            return self._build_result(
                intent=intent,
                cves=[],
                raw_records=[],
                mitre_techniques=[],
                source=source,
                errors=errors,
            )

        cves = self._normalizer.normalize_many(raw_records)
        cves = _apply_version_filter(intent, slots, cves)

        mitre_techniques: list[dict[str, str]] = []
        if intent == "CVE_LOOKUP":
            cwe_ids = _extract_cwe_ids(raw_records)
            mitre_techniques = self._mitre.lookup_by_cwe(cwe_ids)

        return self._build_result(
            intent=intent,
            cves=cves,
            raw_records=raw_records,
            mitre_techniques=mitre_techniques,
            source=source,
            errors=errors,
        )

    def _fallback_cve(self, slots: dict[str, str]) -> NormalizedCVE | None:
        cve_id = slots.get("CVE_ID", "").strip().upper()
        if not cve_id:
            return None
        if not self._kb.exists():
            return None
        for record in self._kb.load():
            if record.cve_id == cve_id:
                return record
        return None

    @staticmethod
    def _build_result(
        *,
        intent: str,
        cves: list[NormalizedCVE],
        raw_records: list[dict[str, Any]],
        mitre_techniques: list[dict[str, str]],
        source: str,
        errors: list[str],
    ) -> dict[str, object]:
        return {
            "intent": intent,
            "source": source,
            "cves": [cve.to_dict() for cve in cves],
            "mitre_techniques": mitre_techniques,
            "errors": errors,
            "raw_count": len(raw_records),
        }


def _resolve_kb_path() -> Path:
    if DEFAULT_KB_PATH.exists():
        return DEFAULT_KB_PATH
    return DEFAULT_SEED_KB_PATH


def _apply_version_filter(
    intent: str,
    slots: dict[str, str],
    cves: list[NormalizedCVE],
) -> list[NormalizedCVE]:
    if intent != "VERSION_SEARCH":
        return cves
    version = slots.get("VERSION", "").strip().lower()
    if not version:
        return cves
    filtered = [
        cve
        for cve in cves
        if any(version in entry.lower() for entry in cve.versions)
    ]
    # Keep unfiltered results when NVD version metadata is sparse.
    return filtered or cves


def _extract_cwe_ids(records: list[Mapping[str, Any]]) -> list[str]:
    cwe_ids: list[str] = []
    seen: set[str] = set()
    for record in records:
        cve = record.get("cve", record)
        if not isinstance(cve, Mapping):
            continue
        weaknesses = cve.get("weaknesses", [])
        if not isinstance(weaknesses, list):
            continue
        for weakness in weaknesses:
            if not isinstance(weakness, Mapping):
                continue
            descriptions = weakness.get("description", [])
            if not isinstance(descriptions, list):
                continue
            for description in descriptions:
                if not isinstance(description, Mapping):
                    continue
                for match in re.findall(r"CWE-\d+", str(description.get("value", "")).upper()):
                    if match not in seen:
                        seen.add(match)
                        cwe_ids.append(match)
    return cwe_ids
