# NLU Models

This directory stores local Phase 2 NLU model artifacts.

Training creates:

```text
models/nlu/bert/
models/nlu/roberta/
models/nlu/evaluation_summary.json
```

Each model-family directory contains:

```text
intent/
ner/
metrics.json
```

## Regeneration

From the project root:

```bash
python3 scripts/train_nlu.py --model-family bert
python3 scripts/train_nlu.py --model-family roberta
```

## Git Policy

Generated model files are ignored by `.gitignore`. This README remains tracked so the directory purpose is documented.
