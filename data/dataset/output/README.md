# Dataset Output

This directory contains the generated NLU training datasets produced by the Phase 1 dataset pipeline.

The files in this directory are generated artifacts. To regenerate them, run:

```bash
python3 scripts/build_dataset.py
```

## Files

- `intents.json`: intent-classification dataset.
- `ner.conll`: named-entity-recognition dataset using BIO tagging in CoNLL-style format.

## `intents.json`

This file stores generated samples grouped by split:

```text
train / validation / test
```

Each sample contains:

- `text`: generated user query.
- `intent`: one of the project intents.
- `entities`: character-level entity spans found in the query.

Example shape:

```json
{
  "text": "What is CVE-2021-44228?",
  "intent": "CVE_LOOKUP",
  "entities": [
    {
      "type": "CVE_ID",
      "value": "CVE-2021-44228",
      "start": 8,
      "end": 22
    }
  ]
}
```

This file is intended for training or evaluating intent-classification components.

## `ner.conll`

This file stores token-level NER annotations.

Each non-comment line follows:

```text
TOKEN TAG
```

Example:

```text
What O
is O
CVE-2021-44228 B-CVE_ID
? O
```

The tags use BIO notation:

- `B-ENTITY`: beginning of an entity.
- `I-ENTITY`: inside/continuation of an entity.
- `O`: outside any entity.

Comment lines beginning with `#` preserve useful metadata such as split, intent, and original text.

## Expected Splits

By default, the builder generates 120 samples:

- Train: 84 samples.
- Validation: 18 samples.
- Test: 18 samples.

The `--samples` option accepts 100 to 1000 samples. The split ratio is 70/15/15 and is validated before files are written.

## Regeneration Notes

The output depends on:

- `data/knowledge_base/cves.json`
- `data/dataset/templates.py`
- `data/dataset/entity_sampler.py`
- `data/dataset/paraphraser.py`
- `data/dataset/bio_annotator.py`
- `data/dataset/pipeline/*`

Changing any of those modules can change the generated output.
