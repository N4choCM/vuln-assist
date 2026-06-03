# NVD Integration

This package contains the integration layer for the National Vulnerability Database (NVD) CVE API.

Its responsibility is limited to external API access. It fetches raw CVE records from NVD and returns structured JSON-like dictionaries. It does not normalize records, generate datasets, annotate entities, or apply business logic.

## Official documentation

| Resource | URL |
|----------|-----|
| CVE API 2.0 (parameters, examples) | [nvd.nist.gov/developers/vulnerabilities](https://nvd.nist.gov/developers/vulnerabilities) |
| Getting started (rate limits, API keys, best practices) | [nvd.nist.gov/developers/start-here](https://nvd.nist.gov/developers/start-here) |
| Request an API key | [nvd.nist.gov/developers/request-an-api-key](https://nvd.nist.gov/developers/request-an-api-key) |

Base endpoint used by this client:

```text
https://services.nvd.nist.gov/rest/json/cves/2.0
```

## Files

- `client.py`: dependency-free NVD API client with pagination, retry logic, and rate-limit throttling.
- `__init__.py`: public exports for the NVD integration package.

## Main classes

- `NVDClientConfig`: runtime configuration for the client, including API URL, API key, page size, timeout, retry count, and request interval.
- `NVDQuery`: supported NVD query parameters, such as CVE ID, keyword search, date ranges, and severity.
- `NVDClient`: client used to fetch CVE records from NVD.

## Usage

```python
from integrations.nvd import NVDClient, NVDQuery

client = NVDClient()
query = NVDQuery(keyword_search="openssl")

records = client.fetch_cves(query=query, total_limit=50)
```

`records` contains raw NVD vulnerability entries. To convert them into the project knowledge-base schema, use `data.knowledge_base.NVDRecordNormalizer`.

Intent-to-query mapping for the dialogue system lives in [`services/query_builder/README.md`](../../services/query_builder/README.md).

## Query parameters (`NVDQuery`)

`NVDQuery.to_params()` maps Python field names to the NVD CVE API query string. Only non-empty fields are sent.

| Python field (`NVDQuery`) | NVD parameter | Meaning |
|-------------------------|---------------|---------|
| `cve_id` | `cveId` | Returns a single CVE by identifier (e.g. `CVE-2021-44228`). NIST marks `cveId` as deprecated in favour of `cveIds`, but this client still uses `cveId` for single lookups. |
| `keyword_search` | `keywordSearch` | Free-text search over the **current CVE description**. Multiple space-separated words behave like AND (all must appear somewhere in the description). NVD applies a trailing wildcard per word (e.g. `circle` matches `circles`). |
| `pub_start_date` | `pubStartDate` | Start of publication window (ISO-8601, e.g. `2021-08-04T00:00:00.000`). Must be used together with `pub_end_date`. Max range: 120 consecutive days. |
| `pub_end_date` | `pubEndDate` | End of publication window (ISO-8601). Required when `pub_start_date` is set. |
| `last_mod_start_date` | `lastModStartDate` | Start of last-modified window (ISO-8601). Must be used together with `last_mod_end_date`. Max range: 120 consecutive days. Recommended for incremental syncs. |
| `last_mod_end_date` | `lastModEndDate` | End of last-modified window (ISO-8601). Required when `last_mod_start_date` is set. |
| `cvss_v3_severity` | `cvssV3Severity` | Filters by CVSS v3 **qualitative** rating. Allowed values: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`. Cannot be combined with `cvssV2Severity` or `cvssV4Severity` in the same request. |

### Date format (ISO-8601)

**ISO-8601** is an international standard for writing dates and times as plain text so they sort correctly and are unambiguous across systems. NVD requires this format for `pubStartDate`, `pubEndDate`, `lastModStartDate`, and `lastModEndDate`.

Pattern used by the CVE API (extended form):

```text
YYYY-MM-DDTHH:MM:SS.sss[Z|±HH:MM]
```

| Part | Meaning |
|------|---------|
| `YYYY-MM-DD` | Calendar date (year, month, day). |
| `T` | Literal separator between date and time (not a timezone). |
| `HH:MM:SS.sss` | Time of day; milliseconds are optional but commonly included. |
| `Z` | UTC (“Zulu” time), e.g. `2023-01-01T00:00:00.000Z`. |
| `±HH:MM` | Offset from UTC, e.g. `2020-01-01T00:00:00.000-05:00` (US Eastern). |

Examples accepted by NVD:

```text
2021-08-04T00:00:00.000
2021-08-04T13:00:00.000+01:00
2020-01-14T23:59:59.999-05:00
```

In query strings, a positive offset `+` must be URL-encoded as `%2B`; `NVDClient` uses `urlencode`, which handles that automatically. Date-range pairs must be supplied together, and the window may span at most **120 consecutive days** (see [official docs](https://nvd.nist.gov/developers/vulnerabilities)).

### Pagination parameters (`NVDClient`)

`NVDClient.fetch_page()` always sends these; callers of `fetch_cves()` do not set them manually.

| Parameter | Set by | Meaning |
|-----------|--------|---------|
| `startIndex` | `NVDClient.fetch_page()` | Zero-based offset into the result set. Increment by the previous page's `resultsPerPage` to fetch the next chunk. |
| `resultsPerPage` | `NVDClient.fetch_page()` | Page size for one response. Defaults to `NVDClientConfig.page_size` (100). NIST recommends keeping the API default where possible. |

Response fields used for pagination: `totalResults`, `resultsPerPage`, `startIndex`, and `vulnerabilities`.

### Parameters not wrapped by this client

The official CVE API supports many additional filters (`cpeName`, `cveIds`, `cweId`, `cvssV3Metrics`, `vulnStatuses`, date ranges, etc.). **This client does not expose them because the project NLU domain only covers CVE identifiers, products, versions, and severity.**

## Client configuration (`NVDClientConfig`)

| Field | Default | Meaning |
|-------|---------|---------|
| `base_url` | CVE 2.0 endpoint | Root URL for all requests. |
| `api_key` | `None` | Optional NVD API key (header `apiKey`). Read from `NVD_API_KEY` via `from_environment()`. |
| `page_size` | `100` | Max `resultsPerPage` per request (capped by remaining `total_limit` in `fetch_cves()`). |
| `timeout_seconds` | `30.0` | HTTP read timeout per request. |
| `max_retries` | `3` | Retries on transient errors (429, 5xx, network/JSON failures). |
| `retry_backoff_seconds` | `2.0` | Base delay for exponential backoff; honours `Retry-After` when present. |
| `min_request_interval_seconds` | `None` | Optional override for minimum seconds between requests. When unset, `effective_request_interval` applies. |
| `effective_request_interval` | computed | **0.6 s** with API key, **6.0 s** without. Aligns with NIST guidance to sleep several seconds between requests and with public rate limits (50 vs 5 requests per rolling 30 s window). |

## API key

The client reads `NVD_API_KEY` from the environment when available:

```bash
export NVD_API_KEY="your-api-key"
```

Using an API key allows a shorter request interval. Without an API key, the client uses a more conservative interval to respect NVD public rate limits.

Request a key at [nvd.nist.gov/developers/request-an-api-key](https://nvd.nist.gov/developers/request-an-api-key). See also `.env.example` at the repository root.

## Layer boundary

This package must not contain:

- CVE normalization logic.
- Dataset generation logic.
- NER or intent-classification logic.
- API orchestration logic.

Those responsibilities belong to `data/knowledge_base`, `data/dataset`, and future backend/service layers respectively.
