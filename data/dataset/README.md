# Dataset Module

This package generates the NLU training dataset for Phase 1.

It produces data for:

- Intent classification.
- Named entity recognition using BIO tags.

The generated samples are grounded in real CVE entities from the normalized knowledge base.

## Responsibilities

This module is responsible for:

- Defining cybersecurity query templates.
- Injecting real entities from `data/knowledge_base`.
- Applying controlled rule-based paraphrasing.
- Producing BIO annotations for NER.
- Building balanced train/validation/test splits.
- Writing generated dataset artifacts.

It must not:

- Fetch external APIs directly.
- Normalize raw NVD records.
- Contain backend/API logic.
- Train models.
- Use uncontrolled LLM generation.

## Files

- `labels.py`: shared intent names, entity types, severity labels, and metric names.
- `models.py`: dataset-domain dataclasses such as `DatasetSample`, `EntitySpan`, and `TokenAnnotation`.
- `templates.py`: parameterized query templates grouped by intent.
- `entity_sampler.py`: samples real CVE IDs, products, versions, severities, and metrics.
- `paraphraser.py`: applies controlled rule-based paraphrases.
- `bio_annotator.py`: tokenizes generated text and assigns BIO tags.
- `AGENTS.md`: local specification for dataset generation rules.
- `__init__.py`: package marker.

## Subdirectories

- [pipeline/](pipeline/README.md): builder, splitter, validator, and writer components.
- [output/](output/README.md): generated dataset files.

## Generation Flow

The dataset is generated through four main steps:

```text
Templates
    -> Entity injection
    -> Rule-based paraphrasing
    -> BIO annotation
```

Then the pipeline:

```text
Build samples
    -> Split train/validation/test
    -> Validate dataset
    -> Write outputs
```

## Intents

The supported intents are defined in `labels.py`:

- `CVE_LOOKUP`
- `CVSS_QUERY`
- `PRODUCT_SEARCH`
- `VERSION_SEARCH`
- `SEVERITY_FILTER`
- `GENERAL_QUERY`

## Entities

The supported entity types are:

- `CVE_ID`
- `PRODUCT`
- `VERSION`
- `SEVERITY`
- `METRIC`

## Outputs

Generated files are written to `data/dataset/output/`:

- `intents.json`
- `ner.conll`

To regenerate them, run from the project root:

```bash
python3 scripts/build_dataset.py
```

## Notes

This package is intentionally modular. Each file owns a specific part of the generation process so future NLU training code can consume the outputs without depending on API, integration, or normalization logic.
