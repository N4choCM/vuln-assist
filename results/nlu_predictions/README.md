# NLU Prediction Results

Prediction outputs produced by manual inference scripts.

## Files

- `bert.json`: readable JSON report for the 120-query manual evaluation set using BERT.
- `roberta.json`: readable JSON report for the 120-query manual evaluation set using RoBERTa.

The `.json` files are overwritten when the manual evaluation is regenerated.

## Regeneration

Single query:

```bash
python scripts/predict_nlu.py --model-family bert --text "What is CVE-2021-44228?" --output-dir results/nlu_predictions
```

Manual 120-query evaluation:

```bash
python scripts/predict_nlu.py \
  --model-family bert \
  --input-file data/evaluation/nlu_manual_queries.json \
  --output-file results/nlu_predictions/bert.json \
  --run-id nlu_manual_120_20260606

python scripts/predict_nlu.py \
  --model-family roberta \
  --input-file data/evaluation/nlu_manual_queries.json \
  --output-file results/nlu_predictions/roberta.json \
  --run-id nlu_manual_120_20260606
```
