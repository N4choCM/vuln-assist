"""Client for the NVD CVE API.

This module is intentionally limited to external API access. It does not
normalize CVE records or apply dataset-specific logic.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class NVDClientConfig:
    """Runtime configuration for the NVD API client."""

    base_url: str = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    api_key: Optional[str] = None
    page_size: int = 100
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_backoff_seconds: float = 2.0
    min_request_interval_seconds: Optional[float] = None

    @classmethod
    def from_environment(cls) -> "NVDClientConfig":
        """Create config using the optional ``NVD_API_KEY`` environment variable."""

        api_key = os.getenv("NVD_API_KEY")
        return cls(api_key=api_key)

    @property
    def effective_request_interval(self) -> float:
        """Return an interval that respects the stricter unauthenticated API pace."""

        if self.min_request_interval_seconds is not None:
            return self.min_request_interval_seconds
        # NVD allows a faster pace with an API key; without one, stay conservative.
        return 0.6 if self.api_key else 6.0


@dataclass(frozen=True)
class NVDQuery:
    """Supported NVD CVE API query parameters."""

    cve_id: Optional[str] = None
    keyword_search: Optional[str] = None
    pub_start_date: Optional[str] = None
    pub_end_date: Optional[str] = None
    last_mod_start_date: Optional[str] = None
    last_mod_end_date: Optional[str] = None
    cvss_v3_severity: Optional[str] = None

    def to_params(self) -> dict[str, str]:
        """Convert the query object to NVD API parameter names."""

        # Attribute names stay Pythonic; keys here match the public NVD API.
        mapping = {
            "cveId": self.cve_id,
            "keywordSearch": self.keyword_search,
            "pubStartDate": self.pub_start_date,
            "pubEndDate": self.pub_end_date,
            "lastModStartDate": self.last_mod_start_date,
            "lastModEndDate": self.last_mod_end_date,
            "cvssV3Severity": self.cvss_v3_severity,
        }
        return {key: value for key, value in mapping.items() if value}


class NVDClient:
    """Small, dependency-free client for paginated CVE retrieval from NVD."""

    def __init__(self, config: Optional[NVDClientConfig] = None) -> None:
        self._config = config or NVDClientConfig.from_environment()
        self._last_request_at: Optional[float] = None

    def fetch_cves(
        self,
        query: Optional[NVDQuery] = None,
        total_limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Fetch CVE vulnerability records, following NVD pagination.

        Returns the raw NVD ``vulnerabilities`` entries as structured JSON-like
        dictionaries. Normalization belongs to ``data.knowledge_base``.
        """

        if total_limit < 1:
            raise ValueError("total_limit must be greater than zero")

        vulnerabilities: list[dict[str, Any]] = []
        start_index = 0
        total_results: Optional[int] = None

        while len(vulnerabilities) < total_limit:
            # Request only what is still needed so the final page does not over-fetch.
            remaining = total_limit - len(vulnerabilities)
            results_per_page = min(self._config.page_size, remaining)
            page = self.fetch_page(
                query=query,
                start_index=start_index,
                results_per_page=results_per_page,
            )
            page_vulnerabilities = self._read_vulnerabilities(page)
            vulnerabilities.extend(page_vulnerabilities)

            # NVD pagination is driven by startIndex plus the reported page size.
            total_results = self._read_int(page, "totalResults", total_results)
            page_count = self._read_int(page, "resultsPerPage", len(page_vulnerabilities))
            if not page_vulnerabilities or page_count <= 0:
                break

            start_index += page_count
            if total_results is not None and start_index >= total_results:
                break

        return vulnerabilities[:total_limit]

    def fetch_page(
        self,
        query: Optional[NVDQuery],
        start_index: int,
        results_per_page: int,
    ) -> dict[str, Any]:
        """Fetch one CVE API page."""

        if start_index < 0:
            raise ValueError("start_index must be non-negative")
        if results_per_page < 1:
            raise ValueError("results_per_page must be greater than zero")

        params = {
            "startIndex": str(start_index),
            "resultsPerPage": str(results_per_page),
        }
        if query is not None:
            params.update(query.to_params())

        # urlencode keeps query construction safe for keywords, dates, and CVE IDs.
        url = f"{self._config.base_url}?{urlencode(params)}"
        return self._request_json(url)

    def _request_json(self, url: str) -> dict[str, Any]:
        # User-Agent identifies this client to the public API.
        headers = {"Accept": "application/json", "User-Agent": "tfg-dataset-builder/1.0"}
        if self._config.api_key:
            headers["apiKey"] = self._config.api_key

        last_error: Optional[Exception] = None
        for attempt in range(self._config.max_retries + 1):
            # Throttle every attempt, including retries, to avoid hammering NVD.
            self._throttle()
            try:
                request = Request(url, headers=headers)
                with urlopen(request, timeout=self._config.timeout_seconds) as response:
                    payload = response.read().decode("utf-8")
                return json.loads(payload)
            except HTTPError as exc:
                last_error = exc
                # Non-transient HTTP errors should surface immediately.
                if not self._is_retryable_http_error(exc) or attempt >= self._config.max_retries:
                    raise
                self._sleep_before_retry(attempt, exc.headers.get("Retry-After"))
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt >= self._config.max_retries:
                    raise RuntimeError("NVD request failed") from exc
                self._sleep_before_retry(attempt, None)

        raise RuntimeError("NVD request failed") from last_error

    def _throttle(self) -> None:
        interval = self._config.effective_request_interval
        if self._last_request_at is not None:
            # monotonic() measures elapsed time safely even if the system clock changes.
            elapsed = time.monotonic() - self._last_request_at
            if elapsed < interval:
                time.sleep(interval - elapsed)
        self._last_request_at = time.monotonic()

    def _sleep_before_retry(self, attempt: int, retry_after: Optional[str]) -> None:
        if retry_after:
            try:
                # Prefer the server-provided wait time when NVD sends Retry-After.
                delay = float(retry_after)
            except ValueError:
                delay = self._config.retry_backoff_seconds * (2**attempt)
        else:
            delay = self._config.retry_backoff_seconds * (2**attempt)
        time.sleep(delay)

    @staticmethod
    def _is_retryable_http_error(error: HTTPError) -> bool:
        return error.code == 429 or 500 <= error.code < 600

    @staticmethod
    def _read_vulnerabilities(page: Mapping[str, Any]) -> list[dict[str, Any]]:
        vulnerabilities = page.get("vulnerabilities", [])
        if not isinstance(vulnerabilities, list):
            return []
        # Keep only object-like entries; malformed items are ignored by the integration.
        return [item for item in vulnerabilities if isinstance(item, dict)]

    @staticmethod
    def _read_int(page: Mapping[str, Any], key: str, fallback: Optional[int]) -> int:
        value = page.get(key, fallback)
        try:
            return int(value)
        except (TypeError, ValueError):
            return int(fallback or 0)
