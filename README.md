# Cybersecurity Vulnerability NLU Dataset Pipeline

This project implements Phase 1 of a hybrid NLP-based conversational system for cybersecurity vulnerability analysis.

The current implementation focuses on the Data & Knowledge Layer:

- Fetch or load CVE records.
- Normalize CVE knowledge.
- Generate NLU training samples.
- Produce intent-classification and NER datasets.

The architecture follows the project rules defined in `AGENTS.md`: modules are separated by responsibility, and no API, NLP, integration, or dataset logic is mixed across layers.

## Current Scope

Implemented:

- NVD integration client.
- CVE knowledge-base normalization and persistence.
- Template-based dataset generation.
- Real entity injection from the knowledge base.
- Rule-based paraphrasing.
- BIO annotation.
- Train/validation/test splitting.
- Dataset validation.
- Output writing.

Not implemented yet:

- Backend API layer.
- Frontend layer.
- NLU model training.
- Dialogue manager.
- Query builder.
- Response generation.
- MITRE integration.

## Project Structure

```text
.
├── AGENTS.md
├── README.md
├── INFORME_PROYECTO.md
├── context/
├── data/
│   ├── knowledge_base/
│   └── dataset/
├── integrations/
│   └── nvd/
└── scripts/
```

## Important Directories

- [integrations/](integrations/README.md): external data-source integrations.
- [integrations/nvd/](integrations/nvd/README.md): NVD CVE API client.
- [data/](data/README.md): project data layer.
- [data/knowledge_base/](data/knowledge_base/README.md): normalized CVE records.
- [data/dataset/](data/dataset/README.md): NLU dataset generation.
- [data/dataset/pipeline/](data/dataset/pipeline/README.md): dataset builder, splitter, validator, and writer.
- [data/dataset/output/](data/dataset/output/README.md): generated dataset artifacts.
- [scripts/](scripts/README.md): executable entry points.
- [context/](context/README.md): project documentation/context files.

Each main directory contains its own README with more specific details.

## Quick Start

From the project root:

```bash
python3 scripts/build_dataset.py
```

This generates:

```text
data/dataset/output/intents.json
data/dataset/output/ner.conll
```

Default output:

- 120 generated samples.
- 84 train samples.
- 18 validation samples.
- 18 test samples.

## Useful Commands

Generate a dataset with a specific size:

```bash
python3 scripts/build_dataset.py --samples 100
```

Write output to another directory:

```bash
python3 scripts/build_dataset.py --output-dir /tmp/tfg-dataset
```

Refresh CVEs from NVD:

```bash
python3 scripts/build_dataset.py --refresh-nvd --nvd-limit 100
```

Filter NVD results by keyword:

```bash
python3 scripts/build_dataset.py --refresh-nvd --nvd-keyword openssl
```

Use an NVD API key:

```bash
export NVD_API_KEY="your-api-key"
python3 scripts/build_dataset.py --refresh-nvd --nvd-limit 100
```

Run a syntax check:

```bash
PYTHONPYCACHEPREFIX=/tmp/tfg-pycache python3 -m compileall integrations data scripts
```

## Generated Outputs

### `intents.json`

JSON dataset for intent classification. It contains generated user queries grouped into:

- `train`
- `validation`
- `test`

Each sample includes text, intent, and character-level entity spans.

### `ner.conll`

CoNLL-style NER dataset using BIO tags:

- `B-ENTITY`
- `I-ENTITY`
- `O`

This file is intended for future NER model training/evaluation.

## Data Flow

```text
scripts/build_dataset.py
    -> data/knowledge_base
    -> data/dataset/pipeline
    -> data/dataset/output
```

With live NVD refresh:

```text
scripts/build_dataset.py
    -> integrations/nvd
    -> data/knowledge_base
    -> data/dataset/pipeline
    -> data/dataset/output
```

## Documentation

- [INFORME_PROYECTO.md](INFORME_PROYECTO.md): detailed Spanish report explaining folders, files, local testing, execution flow, and Mermaid diagrams.
- [context/DATASET_PIPELINE_FLOW.md](context/DATASET_PIPELINE_FLOW.md): beginner-friendly Spanish explanation of the dataset generation flow.
- [integrations/README.md](integrations/README.md): integration layer overview.
- [integrations/nvd/README.md](integrations/nvd/README.md): NVD client details.
- [data/README.md](data/README.md): data layer overview.
- [data/knowledge_base/README.md](data/knowledge_base/README.md): normalized CVE knowledge base.
- [data/dataset/README.md](data/dataset/README.md): dataset generation module.
- [data/dataset/pipeline/README.md](data/dataset/pipeline/README.md): dataset pipeline components.
- [data/dataset/output/README.md](data/dataset/output/README.md): generated outputs.
- [scripts/README.md](scripts/README.md): executable scripts.
- [context/README.md](context/README.md): context directory notes.

## Architecture Boundary

The project must remain modular:

- External API access belongs in `integrations/`.
- Normalized data belongs in `data/knowledge_base/`.
- Dataset generation belongs in `data/dataset/`.
- Executable orchestration belongs in `scripts/`.

Future backend, frontend, NLU, dialogue manager, query builder, and response-generation modules should follow the structure defined in `AGENTS.md`.

## Maintenance Conventions

- Every folder must contain a `README.md`.
- Parent README files should link to child README files.
- When code is created, modified, or removed, update the README in that folder if behavior, usage, purpose, or file lists change.
- Update parent README files when a change affects parent-level understanding.
- Code should include concise comments for non-obvious blocks, such as regex, retries, validation, transformations, pagination, BIO tagging, and architectural boundaries.
- Comments should clarify intent without restating every trivial assignment.
