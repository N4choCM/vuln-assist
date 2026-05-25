from __future__ import annotations

import numpy as np

from services.nlu.metrics import compute_classification_metrics, compute_ner_metrics


def test_classification_metrics_return_standard_scores():
    predictions = np.array([[0.1, 0.9], [0.8, 0.2]])
    labels = np.array([1, 0])

    metrics = compute_classification_metrics((predictions, labels))

    assert metrics["accuracy"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0


def test_ner_metrics_ignore_masked_tokens():
    predictions = np.array(
        [
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [1.0, 0.0, 0.0],
            ]
        ]
    )
    labels = np.array([[-100, 1, 2, 0]])
    id_to_label = {0: "O", 1: "B-CVE_ID", 2: "I-CVE_ID"}

    metrics = compute_ner_metrics((predictions, labels), id_to_label)

    assert metrics["accuracy"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0
