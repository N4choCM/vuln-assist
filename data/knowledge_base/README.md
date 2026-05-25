# Knowledge Base

This package contains the normalized CVE knowledge base used by the dataset generation pipeline.

It is responsible for representing, loading, saving, and normalizing CVE records. It does not generate user queries, BIO tags, or training splits.

## Responsibilities

This module may:

- Define the normalized CVE schema.
- Convert raw NVD records into normalized CVE records.
- Load and save normalized CVEs as JSON.
- Provide the structured data used by `data/dataset`.

This module must not:

- Fetch NVD directly.
- Generate dataset samples.
- Perform paraphrasing.
- Produce NER annotations.
- Contain backend API logic.

## Normalized CVE Schema

Each normalized CVE has this shape:

```json
{
  "cve_id": "CVE-2021-44228",
  "description": "CVE description",
  "cvss_score": 10.0,
  "severity": "CRITICAL",
  "products": ["Apache Log4j"],
  "versions": ["2.14.1"]
}
```

## Files

- `models.py`: defines `NormalizedCVE`, the internal CVE representation used by the project.
- `normalizer.py`: converts raw NVD CVE records into `NormalizedCVE` objects.
- `repository.py`: loads and saves normalized CVE records from/to JSON files.
- `seed_cves.json`: controlled fallback knowledge base with real CVE-derived records.
- `cves.json`: active normalized knowledge base used by the dataset pipeline.
- `mitre_attack_index.json`: local CWE → MITRE ATT&CK technique index for Phase 4 enrichment.
- `__init__.py`: exports the public package interface.

## `seed_cves.json` vs `cves.json`

`seed_cves.json` is the fallback source. It allows the project to work without internet access or a live NVD refresh.

`cves.json` is the active knowledge base loaded by default.

The default flow is:

```text
if cves.json exists:
    load cves.json
else:
    load seed_cves.json
    save it as cves.json
```

When running with `--refresh-nvd`, `cves.json` can be replaced with freshly normalized records from NVD.

## Normalization Flow

Raw NVD records are fetched by `integrations/nvd`.

Then this module normalizes them:

```text
raw NVD JSON
    -> NVDRecordNormalizer
    -> NormalizedCVE
    -> KnowledgeBaseRepository
    -> cves.json
```

The normalizer extracts:

- CVE ID.
- English description when available.
- CVSS score and severity.
- Affected products from CPE data.
- Affected versions or version ranges from CPE data.

## Usage Example

```python
from pathlib import Path

from data.knowledge_base import KnowledgeBaseRepository

repository = KnowledgeBaseRepository(Path("data/knowledge_base/cves.json"))
records = repository.load()
```

To normalize raw NVD records:

```python
from data.knowledge_base import NVDRecordNormalizer

normalizer = NVDRecordNormalizer()
records = normalizer.normalize_many(raw_nvd_records)
```

## Downstream Usage

The dataset layer uses these normalized records to sample real-world entities:

- CVE IDs.
- Products.
- Versions.
- Severities.

This keeps generated NLU examples grounded in real cybersecurity data.
