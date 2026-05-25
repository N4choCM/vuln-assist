"""Map dialogue intents and slots to NVD CVE API queries."""

from __future__ import annotations

from integrations.nvd.client import NVDQuery

# NER may emit mixed casing; keys are normalized before lookup.
_SEVERITY_MAP: dict[str, str] = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
}

# Default page sizes per intent — small limits keep unauthenticated NVD usage viable.
_LIMIT_BY_INTENT: dict[str, int] = {
    "CVE_LOOKUP": 1,
    "CVSS_QUERY": 1,
    "PRODUCT_SEARCH": 20,
    "VERSION_SEARCH": 30,
    "SEVERITY_FILTER": 20,
}


def build_nvd_query(intent: str, slots: dict[str, str]) -> tuple[NVDQuery, int] | None:
    """Return an NVD query and result limit for executable intents, else ``None``."""

    if intent in {"CVE_LOOKUP", "CVSS_QUERY"}:
        cve_id = slots.get("CVE_ID", "").strip().upper()
        if not cve_id:
            return None
        return NVDQuery(cve_id=cve_id), _LIMIT_BY_INTENT[intent]

    if intent == "PRODUCT_SEARCH":
        product = slots.get("PRODUCT", "").strip()
        if not product:
            return None
        return NVDQuery(keyword_search=product), _LIMIT_BY_INTENT[intent]

    if intent == "VERSION_SEARCH":
        product = slots.get("PRODUCT", "").strip()
        version = slots.get("VERSION", "").strip()
        if not product or not version:
            return None
        return NVDQuery(keyword_search=f"{product} {version}"), _LIMIT_BY_INTENT[intent]

    if intent == "SEVERITY_FILTER":
        severity = _map_severity(slots.get("SEVERITY", ""))
        if not severity:
            return None
        product = slots.get("PRODUCT", "").strip()
        return (
            NVDQuery(
                cvss_v3_severity=severity,
                keyword_search=product or None,
            ),
            _LIMIT_BY_INTENT[intent],
        )

    # GENERAL_QUERY and unknown intents never hit external APIs in Phase 4.
    return None


def _map_severity(raw: str) -> str | None:
    normalized = raw.strip().lower()
    if not normalized:
        return None
    return _SEVERITY_MAP.get(normalized)
