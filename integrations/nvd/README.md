# NVD Integration

This package contains the integration layer for the National Vulnerability Database (NVD) CVE API.

Its responsibility is limited to external API access. It fetches raw CVE records from NVD and returns structured JSON-like dictionaries. It does not normalize records, generate datasets, annotate entities, or apply business logic.

## Files

- `client.py`: dependency-free NVD API client with pagination, retry logic, and rate-limit throttling.
- `__init__.py`: public exports for the NVD integration package.

## Main Classes

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

## API Key

The client reads `NVD_API_KEY` from the environment when available:

```bash
export NVD_API_KEY="your-api-key"
```

Using an API key allows a shorter request interval. Without an API key, the client uses a more conservative interval to respect NVD public rate limits.

## Layer Boundary

This package must not contain:

- CVE normalization logic.
- Dataset generation logic.
- NER or intent-classification logic.
- API orchestration logic.

Those responsibilities belong to `data/knowledge_base`, `data/dataset`, and future backend/service layers respectively.
