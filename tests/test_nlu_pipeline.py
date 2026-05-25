from __future__ import annotations

from services.nlu import EntityPrediction, NLUPipeline, NLUResult
from services.nlu.pipeline import _tokenize_for_ner


def test_pipeline_predict_returns_public_dataclass_shape(monkeypatch):
    pipeline = NLUPipeline(model_family="bert")
    entity = EntityPrediction(
        entity_type="CVE_ID",
        value="CVE-2021-44228",
        start=8,
        end=22,
        confidence=0.95,
    )

    monkeypatch.setattr(pipeline, "_load_once", lambda: None)
    monkeypatch.setattr(pipeline, "_predict_intent", lambda text: ("CVE_LOOKUP", 0.9))
    monkeypatch.setattr(pipeline, "_predict_entities", lambda text: [entity])

    result = pipeline.predict("What is CVE-2021-44228?")

    assert isinstance(result, NLUResult)
    assert result.intent == "CVE_LOOKUP"
    assert result.intent_confidence == 0.9
    assert result.entities == [entity]
    assert result.to_dict()["entities"][0]["entity_type"] == "CVE_ID"


def test_entities_from_bio_combines_entity_tokens():
    entities = NLUPipeline._entities_from_bio(
        text="Show Apache 2.4 vulnerabilities",
        label_ids=[0, 1, 3, 0],
        confidences=[0.99, 0.8, 0.9, 0.99],
        offsets=[[0, 4], [5, 11], [12, 15], [16, 31]],
        id_to_label={0: "O", 1: "B-PRODUCT", 3: "B-VERSION"},
    )

    assert [entity.entity_type for entity in entities] == ["PRODUCT", "VERSION"]
    assert entities[0].value == "Apache"
    assert entities[1].value == "2.4"


def test_tokenize_for_ner_keeps_cve_ids_as_one_word_unit():
    assert _tokenize_for_ner("What is CVE-2021-44228?") == [
        ("What", 0, 4),
        ("is", 5, 7),
        ("CVE-2021-44228", 8, 22),
        ("?", 22, 23),
    ]


def test_first_subword_predictions_use_full_word_offsets():
    label_ids, confidences, offsets = NLUPipeline._first_subword_predictions(
        label_ids=[0, 1, 1, 1, 0, 0],
        confidences=[0.99, 0.95, 0.4, 0.3, 0.2, 0.99],
        word_ids=[None, 0, 0, 0, 1, None],
        token_spans=[("CVE-2021-44228", 8, 22), ("?", 22, 23)],
    )

    entities = NLUPipeline._entities_from_bio(
        text="What is CVE-2021-44228?",
        label_ids=label_ids,
        confidences=confidences,
        offsets=offsets,
        id_to_label={0: "O", 1: "B-CVE_ID"},
    )

    assert len(entities) == 1
    assert entities[0].entity_type == "CVE_ID"
    assert entities[0].value == "CVE-2021-44228"
    assert entities[0].confidence == 0.95
