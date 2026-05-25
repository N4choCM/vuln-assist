from __future__ import annotations

import json

from services.nlu.datasets import load_intent_splits, load_ner_splits


def test_load_intent_splits_parses_all_splits(tmp_path):
    dataset_path = tmp_path / "intents.json"
    dataset_path.write_text(
        json.dumps(
            {
                "splits": {
                    "train": [{"text": "What is CVE-2021-44228?", "intent": "CVE_LOOKUP"}],
                    "validation": [
                        {"text": "Show critical CVEs", "intent": "SEVERITY_FILTER"}
                    ],
                    "test": [{"text": "Any vulnerabilities?", "intent": "GENERAL_QUERY"}],
                }
            }
        ),
        encoding="utf-8",
    )

    splits = load_intent_splits(dataset_path)

    assert set(splits) == {"train", "validation", "test"}
    assert splits["train"][0].text == "What is CVE-2021-44228?"
    assert splits["validation"][0].intent == "SEVERITY_FILTER"


def test_load_ner_splits_groups_conll_samples(tmp_path):
    ner_path = tmp_path / "ner.conll"
    ner_path.write_text(
        "\n".join(
            [
                "# split = train",
                "# intent = CVE_LOOKUP",
                "# text = What is CVE-2021-44228?",
                "What O",
                "is O",
                "CVE-2021-44228 B-CVE_ID",
                "? O",
                "",
                "# split = validation",
                "# intent = PRODUCT_SEARCH",
                "# text = Show Apache vulnerabilities",
                "Show O",
                "Apache B-PRODUCT",
                "vulnerabilities O",
                "",
                "# split = test",
                "",
            ]
        ),
        encoding="utf-8",
    )

    splits = load_ner_splits(ner_path)

    assert len(splits["train"]) == 1
    assert splits["train"][0].tokens == ["What", "is", "CVE-2021-44228", "?"]
    assert splits["train"][0].tags == ["O", "O", "B-CVE_ID", "O"]
    assert splits["validation"][0].intent == "PRODUCT_SEARCH"
    assert splits["test"] == []
