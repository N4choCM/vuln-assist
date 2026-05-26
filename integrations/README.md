# Integrations Layer

This directory contains external data-source integrations.

In the project architecture, integrations are responsible only for communication with external systems. They must not contain business logic, NLP logic, dataset generation, API orchestration, or response generation.

## Current Integrations

- [nvd/](nvd/README.md): client for the National Vulnerability Database CVE API.
- [mitre/](mitre/README.md): local MITRE ATT&CK CWE → technique index lookup.
- [llm/](llm/README.md): Ollama HTTP client for Phase 5 response generation.

Future integrations should be added as independent subpackages:

```text
integrations/
├── nvd/
├── mitre/
└── llm/
```

## Responsibilities

Integration modules may:

- Build external API requests.
- Handle authentication or API keys.
- Handle pagination.
- Handle rate limits and retry logic.
- Return raw structured data from the external source.

Integration modules must not:

- Normalize records into the project knowledge-base schema.
- Generate training datasets.
- Perform NER or intent classification.
- Contain backend API routing.
- Mix data-source access with business rules.

## Data Flow

For Phase 1, the integration flow is:

```text
scripts/build_dataset.py
    -> integrations/nvd/NVDClient
    -> raw NVD CVE records
    -> data/knowledge_base/NVDRecordNormalizer
    -> normalized knowledge base
    -> data/dataset pipeline
```

For Phase 4 runtime dialogue retrieval:

```text
backend/services/dialogue_app_service.py
    -> services/query_builder/build_nvd_query
    -> backend/repositories/external_data_repository.py
    -> integrations/nvd/NVDClient
    -> data/knowledge_base/NVDRecordNormalizer
    -> integrations/mitre/MITREAttackCache (CVE_LOOKUP enrichment)
```

The integration layer stops at returning raw CVE records. The knowledge-base layer owns normalization, and the dataset layer owns sample generation.

## Usage Example

```python
from integrations.nvd import NVDClient, NVDQuery

client = NVDClient()
records = client.fetch_cves(
    query=NVDQuery(keyword_search="apache"),
    total_limit=50,
)
```

The returned `records` should be passed to a normalizer before being used by downstream modules.
