# Data Layer

This directory contains the project data layer for Phase 1.

It is split into two independent responsibilities:

- [knowledge_base/](knowledge_base/README.md): normalized CVE records.
- [dataset/](dataset/README.md): generated NLU training data.

The data layer does not contain backend API code, frontend code, or external API clients.

## Structure

```text
data/
├── knowledge_base/
└── dataset/
```

## `knowledge_base/`

See [knowledge_base/README.md](knowledge_base/README.md).

The knowledge-base package stores and manages normalized CVE records.

It owns:

- The normalized CVE schema.
- JSON persistence for CVE records.
- Normalization from raw NVD records to internal project records.

Its active file is:

```text
data/knowledge_base/cves.json
```

If that file does not exist, the pipeline initializes it from:

```text
data/knowledge_base/seed_cves.json
```

## `dataset/`

See [dataset/README.md](dataset/README.md).

The dataset package generates the NLU training data used by future intent-classification and NER modules.

It owns:

- Query templates.
- Entity sampling from the knowledge base.
- Rule-based paraphrasing.
- BIO annotation.
- Train/validation/test splitting.
- Dataset validation.
- Output writing.

Generated files are written to:

```text
data/dataset/output/intents.json
data/dataset/output/ner.conll
```

## Phase 1 Flow

```text
integrations/nvd
    -> data/knowledge_base
    -> data/dataset
    -> data/dataset/output
```

In local fallback mode, the flow starts from `seed_cves.json` instead of NVD:

```text
data/knowledge_base/seed_cves.json
    -> data/knowledge_base/cves.json
    -> data/dataset
    -> data/dataset/output
```

## Regenerating Outputs

From the project root:

```bash
python3 scripts/build_dataset.py
```

This command loads the active knowledge base, generates samples, validates them, and writes the final dataset artifacts.

## Boundary

This directory must not contain:

- React/frontend code.
- FastAPI/backend API code.
- External API HTTP clients.
- Model training code.

Those responsibilities belong to other project layers defined in `AGENTS.md`.
