"""Evaluation metrics for intent classification and BIO NER."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


def compute_classification_metrics(eval_pred: Any) -> dict[str, float]:
    """Compute standard supervised-classification metrics."""

    predictions, labels = _unpack_eval_prediction(eval_pred)
    if isinstance(predictions, tuple):
        predictions = predictions[0]
    predicted_ids = np.argmax(predictions, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        predicted_ids,
        average="weighted",
        zero_division=0,
    )
    return {
        "accuracy": float(accuracy_score(labels, predicted_ids)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }


def compute_ner_metrics(eval_pred: Any, id_to_label: dict[int, str]) -> dict[str, float]:
    """Compute token-level accuracy plus sequence-labeling precision/recall/F1."""

    predictions, labels = _unpack_eval_prediction(eval_pred)
    if isinstance(predictions, tuple):
        predictions = predictions[0]
    predicted_ids = np.argmax(predictions, axis=-1)

    true_sequences: list[list[str]] = []
    predicted_sequences: list[list[str]] = []
    flat_true: list[str] = []
    flat_predicted: list[str] = []

    for prediction_row, label_row in zip(predicted_ids, labels):
        true_tags: list[str] = []
        predicted_tags: list[str] = []
        for prediction_id, label_id in zip(prediction_row, label_row):
            if int(label_id) == -100:
                continue
            true_tag = id_to_label[int(label_id)]
            predicted_tag = id_to_label[int(prediction_id)]
            true_tags.append(true_tag)
            predicted_tags.append(predicted_tag)
            flat_true.append(true_tag)
            flat_predicted.append(predicted_tag)
        true_sequences.append(true_tags)
        predicted_sequences.append(predicted_tags)

    precision, recall, f1 = _sequence_metrics(true_sequences, predicted_sequences)
    return {
        "accuracy": float(accuracy_score(flat_true, flat_predicted)) if flat_true else 0.0,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _sequence_metrics(
    true_sequences: list[list[str]],
    predicted_sequences: list[list[str]],
) -> tuple[float, float, float]:
    try:
        from seqeval.metrics import f1_score, precision_score, recall_score

        return (
            float(precision_score(true_sequences, predicted_sequences, zero_division=0)),
            float(recall_score(true_sequences, predicted_sequences, zero_division=0)),
            float(f1_score(true_sequences, predicted_sequences, zero_division=0)),
        )
    except ImportError:
        # Keep unit tests usable before optional training dependencies are installed.
        flat_true = [tag for sequence in true_sequences for tag in sequence]
        flat_predicted = [tag for sequence in predicted_sequences for tag in sequence]
        precision, recall, f1, _ = precision_recall_fscore_support(
            flat_true,
            flat_predicted,
            average="weighted",
            zero_division=0,
        )
        return float(precision), float(recall), float(f1)


def _unpack_eval_prediction(eval_pred: Any) -> tuple[Any, Any]:
    if hasattr(eval_pred, "predictions") and hasattr(eval_pred, "label_ids"):
        return eval_pred.predictions, eval_pred.label_ids
    return eval_pred
