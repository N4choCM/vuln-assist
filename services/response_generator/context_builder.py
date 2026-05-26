"""Serialize Phase 4 retrieval payloads into LLM-ready context text."""

from __future__ import annotations

MAX_CVES = 3
MAX_PRODUCTS = 5


def build_context(retrieval: dict[str, object]) -> str:
    """Format CVE records and MITRE techniques as plain text for the prompt."""

    lines: list[str] = []
    source = retrieval.get("source", "unknown")
    lines.append(f"Data source: {source}")

    errors = retrieval.get("errors", [])
    if isinstance(errors, list) and errors:
        lines.append(f"Retrieval errors: {'; '.join(str(error) for error in errors)}")

    cves_raw = retrieval.get("cves", [])
    cves = cves_raw if isinstance(cves_raw, list) else []
    for index, entry in enumerate(cves[:MAX_CVES], start=1):
        if not isinstance(entry, dict):
            continue
        lines.append(_format_cve(index, entry))

    techniques_raw = retrieval.get("mitre_techniques", [])
    techniques = techniques_raw if isinstance(techniques_raw, list) else []
    if techniques:
        lines.append("")
        lines.append("MITRE ATT&CK techniques:")
        for item in techniques:
            if not isinstance(item, dict):
                continue
            technique_id = item.get("technique_id", "")
            name = item.get("name", "")
            if technique_id or name:
                lines.append(f"- {technique_id}: {name}".strip(": "))

    return "\n".join(lines)


def _format_cve(index: int, entry: dict[str, object]) -> str:
    cve_id = entry.get("cve_id", "Unknown")
    description = entry.get("description", "")
    score = entry.get("cvss_score", "N/A")
    severity = entry.get("severity", "UNKNOWN")
    products_raw = entry.get("products", [])
    products = products_raw if isinstance(products_raw, list) else []
    product_text = ", ".join(str(product) for product in products[:MAX_PRODUCTS])
    if len(products) > MAX_PRODUCTS:
        product_text += f" (+{len(products) - MAX_PRODUCTS} more)"

    block = [
        f"CVE #{index}: {cve_id}",
        f"  Severity: {severity} (CVSS {score})",
        f"  Description: {description}",
    ]
    if product_text:
        block.append(f"  Affected products: {product_text}")
    return "\n".join(block)
