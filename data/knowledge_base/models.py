"""Knowledge-base domain models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class NormalizedCVE:
    """Normalized CVE record used by the dataset generation layer."""

    cve_id: str
    description: str
    cvss_score: float
    severity: str
    products: list[str]
    versions: list[str]

    @classmethod
    def from_mapping(cls, data: Mapping[str, object]) -> "NormalizedCVE":
        """Build a normalized CVE from JSON data."""

        # JSON input may be incomplete, so every field has a controlled fallback.
        return cls(
            cve_id=str(data.get("cve_id", "")).strip().upper(),
            description=str(data.get("description", "")).strip(),
            cvss_score=float(data.get("cvss_score", 0.0)),
            severity=str(data.get("severity", "UNKNOWN")).strip().upper(),
            products=_read_string_list(data.get("products")),
            versions=_read_string_list(data.get("versions")),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the record using the required knowledge-base schema."""

        return {
            "cve_id": self.cve_id,
            "description": self.description,
            "cvss_score": self.cvss_score,
            "severity": self.severity,
            "products": list(self.products),
            "versions": list(self.versions),
        }


def _read_string_list(value: object) -> list[str]:
    # Strings are Sequences too, but they should not be split into characters.
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    # Convert non-string values safely and drop empty entries after trimming.
    return [str(item).strip() for item in value if str(item).strip()]
