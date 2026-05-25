"""Tests for external data retrieval orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from backend.repositories.external_data_repository import ExternalDataRepository
from data.knowledge_base.models import NormalizedCVE
from data.knowledge_base.repository import KnowledgeBaseRepository
from integrations.mitre.cache import MITREAttackCache
from integrations.nvd.client import NVDQuery


def test_fetch_normalizes_nvd_records() -> None:
    nvd = MagicMock()
    nvd.fetch_cves.return_value = [
        {
            "cve": {
                "id": "CVE-2021-44228",
                "descriptions": [{"lang": "en", "value": "Log4Shell example."}],
                "metrics": {
                    "cvssMetricV31": [
                        {
                            "cvssData": {
                                "baseScore": 10.0,
                                "baseSeverity": "CRITICAL",
                            }
                        }
                    ]
                },
                "weaknesses": [
                    {
                        "description": [{"lang": "en", "value": "CWE-502"}],
                    }
                ],
                "configurations": [],
            }
        }
    ]

    repo = ExternalDataRepository(
        nvd_client=nvd,
        mitre_cache=MITREAttackCache.load(
            Path(__file__).resolve().parents[1] / "data" / "knowledge_base" / "mitre_attack_index.json"
        ),
    )
    result = repo.fetch(
        "CVE_LOOKUP",
        {"CVE_ID": "CVE-2021-44228"},
        NVDQuery(cve_id="CVE-2021-44228"),
        1,
    )

    assert result["source"] == "nvd_live"
    cves = result["cves"]
    assert isinstance(cves, list)
    assert cves[0]["cve_id"] == "CVE-2021-44228"
    techniques = result["mitre_techniques"]
    assert isinstance(techniques, list)
    assert techniques[0]["technique_id"] == "T1190"


def test_fetch_falls_back_to_knowledge_base_on_nvd_error(tmp_path: Path) -> None:
    kb_path = tmp_path / "cves.json"
    KnowledgeBaseRepository(kb_path).save(
        [
            NormalizedCVE(
                cve_id="CVE-2020-1472",
                description="Zerologon example.",
                cvss_score=10.0,
                severity="CRITICAL",
                products=["Microsoft Netlogon"],
                versions=["2019"],
            )
        ]
    )

    nvd = MagicMock()
    nvd.fetch_cves.side_effect = RuntimeError("offline")

    repo = ExternalDataRepository(
        nvd_client=nvd,
        knowledge_base=KnowledgeBaseRepository(kb_path),
    )
    result = repo.fetch(
        "CVSS_QUERY",
        {"CVE_ID": "CVE-2020-1472"},
        NVDQuery(cve_id="CVE-2020-1472"),
        1,
    )

    assert result["source"] == "knowledge_base_fallback"
    cves = result["cves"]
    assert isinstance(cves, list)
    assert cves[0]["cve_id"] == "CVE-2020-1472"
    errors = result["errors"]
    assert isinstance(errors, list)
    assert errors
