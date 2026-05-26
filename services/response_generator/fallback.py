"""Deterministic reply formatting when LLM generation is disabled or fails."""

from __future__ import annotations


def format_retrieval_reply(intent: str, retrieval: dict[str, object]) -> str:
    """Build a minimal structured reply from a Phase 4 retrieval payload."""

    errors = retrieval.get("errors", [])
    if isinstance(errors, list) and errors:
        return "Unable to retrieve vulnerability data from NVD at the moment."

    cves_raw = retrieval.get("cves", [])
    cves = cves_raw if isinstance(cves_raw, list) else []
    if not cves:
        return "No matching vulnerabilities were found."

    first = cves[0] if isinstance(cves[0], dict) else {}

    if intent == "CVSS_QUERY":
        cve_id = first.get("cve_id", "Unknown CVE")
        score = first.get("cvss_score", 0.0)
        severity = first.get("severity", "UNKNOWN")
        return f"{cve_id}: CVSS {score}, severity {severity}."

    if intent == "CVE_LOOKUP":
        cve_id = first.get("cve_id", "Unknown CVE")
        description = first.get("description", "")
        techniques_raw = retrieval.get("mitre_techniques", [])
        techniques = techniques_raw if isinstance(techniques_raw, list) else []
        technique_names = [
            str(item.get("name", ""))
            for item in techniques
            if isinstance(item, dict) and item.get("name")
        ]
        if technique_names:
            joined = ", ".join(technique_names[:3])
            return f"{cve_id}: {description} Related ATT&CK techniques: {joined}."
        return f"{cve_id}: {description}"

    return f"Found {len(cves)} matching vulnerabilities."
