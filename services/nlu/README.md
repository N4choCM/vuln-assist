# NLU Service

This package implements the Natural Language Understanding pipeline.

It trains and serves:

- Intent classification using BERT and RoBERTa.
- Named Entity Recognition using BIO tagging with BERT and RoBERTa.

## Files

- `config.py`: loads NLU configuration and shared paths.
- `datasets.py`: reads datasets and builds HuggingFace-compatible datasets.
- `labels.py`: builds intent and BIO label mappings from shared dataset labels.
- `metrics.py`: computes Accuracy, Precision, Recall, and F1-score.
- `models.py`: dataclasses for samples and runtime prediction results.
- `pipeline.py`: public `NLUPipeline` prediction interface.
- `training.py`: HuggingFace Trainer orchestration for intent and NER models.
- `__init__.py`: package exports.

## Inputs

The service consumes Phase 1 generated artifacts:

```text
data/dataset/output/intents.json
data/dataset/output/ner.conll
```

## Outputs

Training writes local model artifacts and metrics:

```text
models/nlu/bert/
models/nlu/roberta/
models/nlu/evaluation_summary.json
```

## Runtime Interface

```python
from services.nlu import NLUPipeline

pipeline = NLUPipeline(model_family="bert")
result = pipeline.predict("What is the CVSS score of CVE-2021-44228?")
```

`predict()` returns an `NLUResult` containing:

- `text`
- `intent`
- `intent_confidence`
- `entities`

At runtime, NER prediction pre-tokenizes the input with the same cybersecurity token boundaries used by the BIO dataset, then projects HuggingFace subword predictions back to full entities such as `CVE-2021-44228`.

## Training

From the project root:

```bash
python3 scripts/train_nlu.py --model-family bert
python3 scripts/train_nlu.py --model-family roberta
```

## Boundary

This package owns NLU logic only. It must not contain backend routing, frontend logic, external API calls, dialogue management, query building, or response generation.
