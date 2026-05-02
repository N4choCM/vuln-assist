"""Shared dataset labels."""

from __future__ import annotations


# Keep intent labels centralized so templates, builders, and validators stay aligned.
INTENTS: tuple[str, ...] = (
    "CVE_LOOKUP",
    "CVSS_QUERY",
    "PRODUCT_SEARCH",
    "VERSION_SEARCH",
    "SEVERITY_FILTER",
    "GENERAL_QUERY",
)

# BIO tags are derived from this entity-type inventory.
ENTITY_TYPES: tuple[str, ...] = (
    "CVE_ID",
    "PRODUCT",
    "VERSION",
    "SEVERITY",
    "METRIC",
)

# Fallback severities used when a KB record has no concrete severity.
SEVERITIES: tuple[str, ...] = ("low", "medium", "high", "critical")

# Metric mentions provide realistic CVSS-related slots for templates.
METRICS: tuple[str, ...] = (
    "CVSS",
    "CVSS score",
    "CVSS base score",
    "attack vector",
    "base severity",
    "exploitability score",
)
