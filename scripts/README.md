# Scripts

This directory contains executable entry points for project tasks.

Scripts should stay thin: they may parse command-line arguments and orchestrate project modules, but they must not contain core business logic, NLP logic, normalization logic, or dataset-generation internals.

## Files

- `build_dataset.py`: runs the complete Phase 1 dataset generation pipeline.
- `train_nlu.py`: trains Phase 2 intent and NER models.
- `predict_nlu.py`: runs prediction with a trained Phase 2 NLU model.

## `build_dataset.py`

This script builds the NLU dataset used for intent classification and NER.

```bash
python3 scripts/build_dataset.py
```

It writes:

```text
data/dataset/output/intents.json
data/dataset/output/ner.conll
```

Useful options:

```bash
python3 scripts/build_dataset.py --samples 120
python3 scripts/build_dataset.py --samples 1000
python3 scripts/build_dataset.py --seed 7
python3 scripts/build_dataset.py --output-dir /tmp/tfg-dataset
python3 scripts/build_dataset.py --refresh-nvd --nvd-limit 100
python3 scripts/build_dataset.py --refresh-nvd --nvd-keyword apache
```

## `train_nlu.py`

This script trains HuggingFace BERT and RoBERTa models for:

- Intent classification.
- BIO NER.

Train all configured model families:

```bash
python3 scripts/train_nlu.py
```

Train one model family:

```bash
python3 scripts/train_nlu.py --model-family bert
python3 scripts/train_nlu.py --model-family roberta
```

Outputs are written to:

```text
models/nlu/
```

## `predict_nlu.py`

This script loads a trained NLU model family and prints structured JSON.

```bash
python3 scripts/predict_nlu.py --model-family bert --text "What is CVE-2021-44228?"
```

## Serving the Phase 3 Dialogue API

The FastAPI orchestration stack lives outside this folder (see [`../backend/README.md`](../backend/README.md)). Typical local launch:

```bash
NLU_MODEL_FAMILY=bert uvicorn backend.api.main:app --reload
```

## Boundary

Scripts in this directory should delegate to modules under:

- `integrations/`
- `data/knowledge_base/`
- `data/dataset/`
- `services/nlu/`

They should not become monolithic pipelines.
