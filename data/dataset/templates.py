"""Parameterized cybersecurity query templates."""

from __future__ import annotations

import re
from dataclasses import dataclass

from data.dataset.labels import INTENTS


# Captures placeholder names inside braces, e.g. {CVE_ID} -> CVE_ID.
_PLACEHOLDER_PATTERN = re.compile(r"{([A-Z_]+)}")


@dataclass(frozen=True)
class QueryTemplate:
    """A template for a user query tied to one intent."""

    intent: str
    text: str

    @property
    def placeholders(self) -> tuple[str, ...]:
        # Return only placeholder names, not the surrounding braces.
        return tuple(_PLACEHOLDER_PATTERN.findall(self.text))

    def render(self, values: dict[str, str]) -> str:
        rendered = self.text
        for placeholder in self.placeholders:
            # Values are already sampled and validated by EntitySampler.
            rendered = rendered.replace("{" + placeholder + "}", values[placeholder])
        return rendered


# Templates are grouped by intent to keep generation balanced and auditable.
TEMPLATES: dict[str, tuple[QueryTemplate, ...]] = {
    "CVE_LOOKUP": (
        QueryTemplate("CVE_LOOKUP", "What is {CVE_ID}?"),
        QueryTemplate("CVE_LOOKUP", "Give me details about {CVE_ID}."),
        QueryTemplate("CVE_LOOKUP", "Explain {CVE_ID}."),
        QueryTemplate("CVE_LOOKUP", "Summarize the vulnerability {CVE_ID}."),
        QueryTemplate("CVE_LOOKUP", "I need information on {CVE_ID}."),
        QueryTemplate("CVE_LOOKUP", "What does {CVE_ID} affect?"),
    ),
    "CVSS_QUERY": (
        QueryTemplate("CVSS_QUERY", "What is the {METRIC} for {CVE_ID}?"),
        QueryTemplate("CVSS_QUERY", "Show the {METRIC} of {CVE_ID}."),
        QueryTemplate("CVSS_QUERY", "How severe is {CVE_ID} according to {METRIC}?"),
        QueryTemplate("CVSS_QUERY", "Give me the {METRIC} assigned to {CVE_ID}."),
        QueryTemplate("CVSS_QUERY", "What {METRIC} does {CVE_ID} have?"),
        QueryTemplate("CVSS_QUERY", "Check the {METRIC} for {CVE_ID}."),
    ),
    "PRODUCT_SEARCH": (
        QueryTemplate("PRODUCT_SEARCH", "Show vulnerabilities in {PRODUCT}."),
        QueryTemplate("PRODUCT_SEARCH", "Find CVEs affecting {PRODUCT}."),
        QueryTemplate("PRODUCT_SEARCH", "Which vulnerabilities impact {PRODUCT}?"),
        QueryTemplate("PRODUCT_SEARCH", "List known CVEs for {PRODUCT}."),
        QueryTemplate("PRODUCT_SEARCH", "Search for {SEVERITY} vulnerabilities in {PRODUCT}."),
        QueryTemplate("PRODUCT_SEARCH", "What security issues are known for {PRODUCT}?"),
    ),
    "VERSION_SEARCH": (
        QueryTemplate("VERSION_SEARCH", "Show vulnerabilities in {PRODUCT} {VERSION}."),
        QueryTemplate("VERSION_SEARCH", "Does {PRODUCT} version {VERSION} have known CVEs?"),
        QueryTemplate("VERSION_SEARCH", "Find CVEs affecting {PRODUCT} {VERSION}."),
        QueryTemplate("VERSION_SEARCH", "List vulnerabilities for {PRODUCT} version {VERSION}."),
        QueryTemplate("VERSION_SEARCH", "Check whether {PRODUCT} {VERSION} is vulnerable."),
        QueryTemplate("VERSION_SEARCH", "What CVEs affect {PRODUCT} release {VERSION}?"),
    ),
    "SEVERITY_FILTER": (
        QueryTemplate("SEVERITY_FILTER", "Show {SEVERITY} vulnerabilities."),
        QueryTemplate("SEVERITY_FILTER", "Find {SEVERITY} CVEs."),
        QueryTemplate("SEVERITY_FILTER", "List vulnerabilities with {SEVERITY} severity."),
        QueryTemplate("SEVERITY_FILTER", "Which {SEVERITY} vulnerabilities affect {PRODUCT}?"),
        QueryTemplate("SEVERITY_FILTER", "Search for {SEVERITY} security issues in {PRODUCT}."),
        QueryTemplate("SEVERITY_FILTER", "Give me CVEs rated {SEVERITY}."),
    ),
    "GENERAL_QUERY": (
        QueryTemplate("GENERAL_QUERY", "What is a CVE?"),
        QueryTemplate("GENERAL_QUERY", "How does {METRIC} work?"),
        QueryTemplate("GENERAL_QUERY", "What does the NVD provide?"),
        QueryTemplate("GENERAL_QUERY", "Explain vulnerability severity."),
        QueryTemplate("GENERAL_QUERY", "What information is stored in a vulnerability record?"),
        QueryTemplate("GENERAL_QUERY", "How are software vulnerabilities classified?"),
        QueryTemplate("GENERAL_QUERY", "What does {SEVERITY} severity mean?"),
        QueryTemplate("GENERAL_QUERY", "How should I interpret a {METRIC}?"),
        QueryTemplate("GENERAL_QUERY", "What is vulnerability disclosure?"),
        QueryTemplate("GENERAL_QUERY", "How do CVE records relate to affected products?"),
        QueryTemplate("GENERAL_QUERY", "Why do analysts use the NVD?"),
        QueryTemplate("GENERAL_QUERY", "What fields are useful in CVE analysis?"),
    ),
}


def all_templates() -> tuple[QueryTemplate, ...]:
    """Return all templates in intent order."""

    templates: list[QueryTemplate] = []
    for intent in INTENTS:
        # INTENTS defines the canonical order used across the dataset package.
        templates.extend(TEMPLATES[intent])
    return tuple(templates)
