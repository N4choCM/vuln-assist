# Scripts

This directory contains executable entry points for project tasks.

Scripts should stay thin: they may parse command-line arguments and orchestrate project modules, but they must not contain core business logic, NLP logic, normalization logic, or dataset-generation internals.

## Files

- `build_dataset.py`: runs the complete Phase 1 dataset generation pipeline.

## `build_dataset.py`

This script builds the NLU dataset used for future intent classification and NER.

It orchestrates:

```text
Knowledge base loading
    -> Dataset generation
    -> Train/validation/test splitting
    -> Validation
    -> Output writing
```

## Basic Usage

From the project root:

```bash
python3 scripts/build_dataset.py
```

This generates:

```text
data/dataset/output/intents.json
data/dataset/output/ner.conll
```

## Useful Options

Set the number of generated samples:

```bash
python3 scripts/build_dataset.py --samples 120
```

Use a different deterministic seed:

```bash
python3 scripts/build_dataset.py --seed 7
```

Write outputs to another directory:

```bash
python3 scripts/build_dataset.py --output-dir /tmp/tfg-dataset
```

Refresh the knowledge base from NVD:

```bash
python3 scripts/build_dataset.py --refresh-nvd --nvd-limit 100
```

Filter NVD results by keyword:

```bash
python3 scripts/build_dataset.py --refresh-nvd --nvd-keyword apache
```

## Expected Output

With the default configuration, the script generates 120 samples:

- 84 train samples.
- 18 validation samples.
- 18 test samples.

The script validates the dataset before writing output files.

## Boundary

Scripts in this directory should delegate to modules under:

- `integrations/`
- `data/knowledge_base/`
- `data/dataset/`

They should not become monolithic pipelines.
