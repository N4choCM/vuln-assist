# Query Builder (`services/query_builder`)

Maps dialogue intents and filled slots to [NVD CVE API](../integrations/nvd/README.md) queries.

## Usage

```python
from services.query_builder import build_nvd_query

query, limit = build_nvd_query("CVE_LOOKUP", {"CVE_ID": "CVE-2021-44228"})
```

## Intent mapping

| Intent | NVD parameters | Limit |
|--------|----------------|-------|
| `CVE_LOOKUP` / `CVSS_QUERY` | `cve_id` | 1 |
| `PRODUCT_SEARCH` | `keyword_search` | 20 |
| `VERSION_SEARCH` | `keyword_search` (`product version`) | 30 |
| `SEVERITY_FILTER` | `cvss_v3_severity` (+ optional `keyword_search`) | 20 |
| `GENERAL_QUERY` | not executed | — |

Version filtering after fetch is handled in [`backend/repositories/external_data_repository.py`](../../backend/repositories/external_data_repository.py).
