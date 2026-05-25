#!/usr/bin/env python3
"""Build a local CWE → MITRE ATT&CK technique index from the public STIX bundle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.request import urlopen

DEFAULT_STIX_URL = (
    "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "knowledge_base" / "mitre_attack_index.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_STIX_URL, help="Enterprise ATT&CK STIX bundle URL")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JSON index path")
    args = parser.parse_args()

    bundle = _download_json(str(args.url))
    index = _build_index(bundle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(index, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"Wrote {len(index)} CWE mappings to {args.output}")
    return 0


def _download_json(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("STIX bundle must be a JSON object")
    return payload


def _build_index(bundle: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    objects = bundle.get("objects", [])
    if not isinstance(objects, list):
        return {}

    techniques: dict[str, dict[str, str]] = {}
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        if obj.get("type") != "attack-pattern":
            continue
        external_refs = obj.get("external_references", [])
        technique_id = ""
        if isinstance(external_refs, list):
            for ref in external_refs:
                if isinstance(ref, dict) and ref.get("source_name") == "mitre-attack":
                    technique_id = str(ref.get("external_id", "")).strip()
                    break
        if not technique_id:
            continue
        techniques[str(obj.get("id", ""))] = {
            "technique_id": technique_id,
            "name": str(obj.get("name", "")).strip(),
        }

    index: dict[str, list[dict[str, str]]] = {}
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        if obj.get("type") != "relationship":
            continue
        if obj.get("relationship_type") != "related-to":
            continue
        source_ref = str(obj.get("source_ref", ""))
        target_ref = str(obj.get("target_ref", ""))
        if not source_ref.startswith("attack-pattern--"):
            continue
        if not target_ref.startswith("weakness--"):
            continue
        technique = techniques.get(source_ref)
        cwe_id = _cwe_from_weakness(objects, target_ref)
        if technique is None or cwe_id is None:
            continue
        index.setdefault(cwe_id, [])
        if technique not in index[cwe_id]:
            index[cwe_id].append(technique)

    return index


def _cwe_from_weakness(objects: list[Any], weakness_ref: str) -> str | None:
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        if obj.get("type") != "weakness":
            continue
        if str(obj.get("id", "")) != weakness_ref:
            continue
        external_refs = obj.get("external_references", [])
        if not isinstance(external_refs, list):
            return None
        for ref in external_refs:
            if isinstance(ref, dict) and ref.get("source_name") == "cwe":
                external_id = str(ref.get("external_id", "")).strip().upper()
                if external_id.startswith("CWE-"):
                    return external_id
    return None


if __name__ == "__main__":
    sys.exit(main())
