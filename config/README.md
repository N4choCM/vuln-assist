# Configuration

This directory contains project configuration files.

## Files

- `nlu_training.json`: Phase 2 NLU training defaults for BERT and RoBERTa.

## `nlu_training.json`

The NLU config defines:

- HuggingFace model names for `bert` and `roberta`.
- Learning rate.
- Batch size.
- Maximum token length.
- Early stopping patience.
- Random seed.
- Number of training epochs.

The config is read by:

```text
services/nlu/config.py
scripts/train_nlu.py
scripts/predict_nlu.py
```

## Boundary

Configuration files may define settings, but they must not contain executable logic or hardcoded business rules.
