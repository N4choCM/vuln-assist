# Configuration

This directory contains project configuration files.

## Files

- `nlu_training.json`: Phase 2 NLU training defaults for BERT and RoBERTa.
- `response_generator.json`: Phase 5 Ollama generation defaults (temperature, model, timeout).

Python dependencies:

- [`requirements.txt`](../requirements.txt): full dev install (includes `pytest`).
- [`requirements-prod.txt`](../requirements-prod.txt): runtime-only deps used by [`deploy/Dockerfile.api`](../deploy/Dockerfile.api).

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

## `response_generator.json`

Phase 5 defaults read by [`services/response_generator/config.py`](../services/response_generator/config.py):

- Ollama base URL and model name.
- Temperature and max tokens.
- HTTP timeout.

Override at runtime with `RESPONSE_GENERATOR_ENABLED`, `LLM_PROVIDER`, `OLLAMA_BASE_URL`, and `OLLAMA_MODEL` (see [`.env.example`](../.env.example)).

## Boundary

Configuration files may define settings, but they must not contain executable logic or hardcoded business rules.
