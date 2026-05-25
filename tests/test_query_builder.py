"""Unit tests for intent-to-NVD query mapping."""

from __future__ import annotations

from services.query_builder import build_nvd_query


def test_cve_lookup_maps_cve_id() -> None:
    query, limit = build_nvd_query("CVE_LOOKUP", {"CVE_ID": "cve-2021-44228"})  # type: ignore[misc]
    assert query.cve_id == "CVE-2021-44228"
    assert limit == 1


def test_cvss_query_maps_cve_id() -> None:
    query, limit = build_nvd_query("CVSS_QUERY", {"CVE_ID": "CVE-2020-1472"})  # type: ignore[misc]
    assert query.cve_id == "CVE-2020-1472"
    assert limit == 1


def test_product_search_uses_keyword() -> None:
    query, limit = build_nvd_query("PRODUCT_SEARCH", {"PRODUCT": "Apache"})  # type: ignore[misc]
    assert query.keyword_search == "Apache"
    assert limit == 20


def test_version_search_combines_product_and_version() -> None:
    query, limit = build_nvd_query(  # type: ignore[misc]
        "VERSION_SEARCH",
        {"PRODUCT": "OpenSSL", "VERSION": "1.1.1"},
    )
    assert query.keyword_search == "OpenSSL 1.1.1"
    assert limit == 30


def test_severity_filter_maps_severity() -> None:
    query, limit = build_nvd_query("SEVERITY_FILTER", {"SEVERITY": "Critical"})  # type: ignore[misc]
    assert query.cvss_v3_severity == "CRITICAL"
    assert query.keyword_search is None
    assert limit == 20


def test_severity_filter_includes_optional_product() -> None:
    query, _ = build_nvd_query(  # type: ignore[misc]
        "SEVERITY_FILTER",
        {"SEVERITY": "high", "PRODUCT": "Apache"},
    )
    assert query.cvss_v3_severity == "HIGH"
    assert query.keyword_search == "Apache"


def test_general_query_returns_none() -> None:
    assert build_nvd_query("GENERAL_QUERY", {}) is None


def test_missing_slots_return_none() -> None:
    assert build_nvd_query("CVE_LOOKUP", {}) is None
    assert build_nvd_query("PRODUCT_SEARCH", {}) is None
