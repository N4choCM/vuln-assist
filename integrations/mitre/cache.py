"""Local MITRE ATT&CK index for CWE-to-technique enrichment."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

DEFAULT_INDEX_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "knowledge_base" / "mitre_attack_index.json"
)


class MITREAttackCache:
    """Read-only lookup over a pre-built CWE → ATT&CK technique index."""

    def __init__(self, index: Mapping[str, list[dict[str, str]]]) -> None:
        self._index = index

    @classmethod
    def load_default(cls) -> "MITREAttackCache":
        """Load the bundled index from ``data/knowledge_base/mitre_attack_index.json``."""

        return cls.load(DEFAULT_INDEX_PATH)

    @classmethod
    def load(cls, path: Path) -> "MITREAttackCache":
        if not path.exists():
            return cls({})
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            return cls({})
        return cls(_normalize_index(payload))

    def lookup_by_cwe(self, cwe_ids: list[str]) -> list[dict[str, str]]:
        """Return unique ATT&CK techniques linked to any of the given CWE IDs."""

        seen: set[str] = set()
        techniques: list[dict[str, str]] = []
        for cwe_id in cwe_ids:
            normalized = _normalize_cwe_id(cwe_id)
            for entry in self._index.get(normalized, []):
                technique_id = entry.get("technique_id", "")
                if not technique_id or technique_id in seen:
                    continue
                seen.add(technique_id)
                techniques.append(
                    {
                        "technique_id": technique_id,
                        "name": entry.get("name", ""),
                    }
                )
        return techniques


def _normalize_index(payload: Mapping[str, Any]) -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = {}
    for key, value in payload.items():
        cwe_id = _normalize_cwe_id(str(key))
        if not cwe_id or not isinstance(value, list):
            continue
        entries: list[dict[str, str]] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            technique_id = str(item.get("technique_id", "")).strip()
            if not technique_id:
                continue
            entries.append(
                {
                    "technique_id": technique_id,
                    "name": str(item.get("name", "")).strip(),
                }
            )
        if entries:
            index[cwe_id] = entries
    return index


def _normalize_cwe_id(raw: str) -> str:
    cleaned = raw.strip().upper()
    if cleaned.startswith("CWE-"):
        return cleaned
    if cleaned.startswith("CWE"):
        suffix = cleaned[3:].lstrip("-")
        return f"CWE-{suffix}" if suffix else cleaned
    if cleaned.isdigit():
        return f"CWE-{cleaned}"
    return cleaned
