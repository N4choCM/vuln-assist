# Dataset Pipeline

This package contains the orchestration components for generating the NLU dataset.

It belongs to the dataset layer. It does not fetch external data directly and does not contain API/backend logic. Its job is to coordinate dataset-specific steps using the lower-level dataset modules.

## Files

- `builder.py`: generates `DatasetSample` objects from templates, sampled entities, paraphrases, and BIO annotations.
- `splitter.py`: creates train, validation, and test splits.
- `validator.py`: validates dataset size, intent coverage, split ratios, entity spans, duplicates, and BIO consistency.
- `writer.py`: writes the final `intents.json` and `ner.conll` output files.
- `__init__.py`: exports the main pipeline classes.

## Execution Order

The pipeline is called by `scripts/build_dataset.py` in this order:

```text
DatasetBuilder
    -> DatasetSplitter
    -> DatasetValidator
    -> DatasetWriter
```

## `DatasetBuilder`

`DatasetBuilder` creates the generated samples.

It uses:

- `data/dataset/templates.py` for parameterized query templates.
- `data/dataset/entity_sampler.py` for real entities from the knowledge base.
- `data/dataset/paraphraser.py` for controlled rule-based paraphrasing.
- `data/dataset/bio_annotator.py` for BIO NER labels.
- `data/dataset/models.py` for shared sample and annotation models.

The builder also keeps intent distribution balanced and avoids duplicate generated texts.

## `DatasetSplitter`

`DatasetSplitter` divides generated samples into:

- `train`
- `validation`
- `test`

The target ratio is 70/15/15. The splitter allocates samples by intent so the resulting splits stay balanced.

## `DatasetValidator`

`DatasetValidator` checks that generated data is usable before writing files.

It validates:

- Total sample count is between 100 and 1000.
- All intents are represented.
- No unknown intents are present.
- Splits are exactly `train`, `validation`, and `test`.
- No duplicate text appears across splits.
- Split ratios are close to 70/15/15.
- Entity spans match the original text.
- BIO tags are structurally valid.

If validation fails, the pipeline raises an error before writing output.

## `DatasetWriter`

`DatasetWriter` persists the generated data to:

```text
data/dataset/output/intents.json
data/dataset/output/ner.conll
```

`intents.json` is intended for intent classification. `ner.conll` is intended for NER training/evaluation with BIO labels.

## Boundary

This package must not:

- Call the NVD API directly.
- Normalize raw external CVE records.
- Implement backend API routes.
- Train NLU models.

Those responsibilities belong to `integrations/nvd`, `data/knowledge_base`, future backend modules, and future model-training modules respectively.
