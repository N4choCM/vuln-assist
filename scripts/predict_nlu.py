#!/usr/bin/env python3
"""Run prediction with a trained Phase 2 NLU model."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREDICTION_OUTPUT_DIR = PROJECT_ROOT / "results" / "nlu_predictions"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.nlu import NLUPipeline
from services.nlu.config import DEFAULT_CONFIG_PATH, DEFAULT_MODELS_DIR


def append_prediction_record(
    output_dir: Path,
    model_family: str,
    payload: dict[str, object],
) -> Path:
    """Append one JSONL record per model family without overwriting prior runs."""

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{model_family}.jsonl"
    with output_path.open("a", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False)
        file.write("\n")
    return output_path


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    pipeline = NLUPipeline(
        model_family=args.model_family,
        models_dir=args.models_dir,
        config_path=args.config,
    )

    if args.input_file is not None:
        records = load_prediction_inputs(args.input_file)
        payload = run_batch_predictions(
            pipeline=pipeline,
            records=records,
            model_family=args.model_family,
            input_file=args.input_file,
            models_dir=args.models_dir,
            config_path=args.config,
            run_id=args.run_id,
        )
        write_or_print_json(payload, args.output_file)
        return 0

    if args.text is None:
        raise ValueError("--text is required unless --input-file is provided.")

    result = pipeline.predict(args.text)
    result_payload = result.to_dict()
    write_or_print_json(result_payload, args.output_file)

    if args.output_dir is not None:
        record = {
            **result_payload,
            "model_family": args.model_family,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        if args.run_id:
            record["run_id"] = args.run_id
        output_path = append_prediction_record(
            args.output_dir,
            args.model_family,
            record,
        )
        print(f"- appended record to {output_path}", file=sys.stderr)

    return 0


def load_prediction_inputs(input_file: Path) -> list[dict[str, Any]]:
    """Load a batch of texts, optionally including expected labels."""

    with input_file.open(encoding="utf-8") as file:
        payload = json.load(file)

    if isinstance(payload, dict):
        raw_records = payload.get("queries") or payload.get("records") or payload.get("items")
    else:
        raw_records = payload

    if not isinstance(raw_records, list):
        raise ValueError("Batch input must be a JSON list or an object with a queries list.")

    records: list[dict[str, Any]] = []
    for index, raw_record in enumerate(raw_records, start=1):
        if isinstance(raw_record, str):
            records.append(
                {
                    "id": f"query_{index:03d}",
                    "text": raw_record,
                    "expected_entities": [],
                }
            )
            continue
        if not isinstance(raw_record, dict):
            raise ValueError(f"Invalid query record at position {index}: expected string or object.")
        text = raw_record.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Invalid query record at position {index}: missing non-empty text.")
        records.append(
            {
                "id": raw_record.get("id") or f"query_{index:03d}",
                "text": text,
                "expected_intent": raw_record.get("expected_intent"),
                "expected_entities": raw_record.get("expected_entities", []),
            }
        )
    return records


def run_batch_predictions(
    pipeline: NLUPipeline,
    records: list[dict[str, Any]],
    model_family: str,
    input_file: Path,
    models_dir: Path,
    config_path: Path,
    run_id: str,
) -> dict[str, Any]:
    """Predict all batch records and return a report-friendly JSON payload."""

    recorded_at = datetime.now(timezone.utc).isoformat()
    effective_run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    results: list[dict[str, Any]] = []

    for record in records:
        prediction = pipeline.predict(record["text"]).to_dict()
        prediction_without_text = {key: value for key, value in prediction.items() if key != "text"}
        result_record: dict[str, Any] = {
            "id": record["id"],
            "text": record["text"],
            "expected_intent": record.get("expected_intent"),
            "expected_entities": record.get("expected_entities", []),
            "prediction": prediction_without_text,
        }

        expected_intent = record.get("expected_intent")
        if expected_intent is not None:
            result_record["intent_correct"] = expected_intent == prediction["intent"]

        expected_entities = record.get("expected_entities", [])
        if expected_entities is not None:
            result_record["entity_exact_match"] = _entity_signature(
                expected_entities
            ) == _entity_signature(prediction["entities"])

        results.append(result_record)

    return {
        "model_family": model_family,
        "run_id": effective_run_id,
        "recorded_at": recorded_at,
        "input_file": str(input_file),
        "models_dir": str(models_dir),
        "config": str(config_path),
        "summary": summarize_batch(results),
        "results": results,
    }


def summarize_batch(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Build compact metrics for a report appendix."""

    total = len(results)
    intent_prf = _intent_precision_recall_f1(results)
    entity_prf = _entity_precision_recall_f1(results)
    intent_evaluable = [result for result in results if result.get("expected_intent") is not None]
    entity_evaluable = [result for result in results if result.get("expected_entities") is not None]
    intent_confidences = [
        float(result["prediction"]["intent_confidence"])
        for result in results
        if result.get("prediction")
    ]
    entity_confidences = [
        float(entity["confidence"])
        for result in results
        for entity in result["prediction"].get("entities", [])
    ]
    predicted_intents = Counter(
        result["prediction"]["intent"] for result in results if result.get("prediction")
    )
    expected_intents = Counter(
        result["expected_intent"]
        for result in results
        if result.get("expected_intent") is not None
    )

    per_intent: dict[str, dict[str, Any]] = {}
    for intent in sorted(expected_intents):
        rows = [result for result in intent_evaluable if result["expected_intent"] == intent]
        per_intent[intent] = {
            "total": len(rows),
            "intent_accuracy": _ratio(
                sum(1 for result in rows if result.get("intent_correct")),
                len(rows),
            ),
            "entity_exact_match_rate": _ratio(
                sum(1 for result in rows if result.get("entity_exact_match")),
                len(rows),
            ),
            "mean_intent_confidence": _mean(
                float(result["prediction"]["intent_confidence"]) for result in rows
            ),
        }

    return {
        "total": total,
        "intent_accuracy": _ratio(
            sum(1 for result in intent_evaluable if result.get("intent_correct")),
            len(intent_evaluable),
        ),
        "intent_precision_macro": intent_prf["macro"]["precision"],
        "intent_recall_macro": intent_prf["macro"]["recall"],
        "intent_f1_macro": intent_prf["macro"]["f1"],
        "intent_precision_weighted": intent_prf["weighted"]["precision"],
        "intent_recall_weighted": intent_prf["weighted"]["recall"],
        "intent_f1_weighted": intent_prf["weighted"]["f1"],
        "entity_exact_match_rate": _ratio(
            sum(1 for result in entity_evaluable if result.get("entity_exact_match")),
            len(entity_evaluable),
        ),
        "entity_precision": entity_prf["precision"],
        "entity_recall": entity_prf["recall"],
        "entity_f1": entity_prf["f1"],
        "mean_intent_confidence": _mean(intent_confidences),
        "min_intent_confidence": min(intent_confidences) if intent_confidences else None,
        "max_intent_confidence": max(intent_confidences) if intent_confidences else None,
        "mean_entity_confidence": _mean(entity_confidences),
        "low_intent_confidence_lt_0_70": sum(
            1 for confidence in intent_confidences if confidence < 0.70
        ),
        "intent_confidence_gte_0_90": sum(
            1 for confidence in intent_confidences if confidence >= 0.90
        ),
        "expected_intent_counts": dict(sorted(expected_intents.items())),
        "predicted_intent_counts": dict(sorted(predicted_intents.items())),
        "per_intent": per_intent,
    }


def _intent_precision_recall_f1(results: list[dict[str, Any]]) -> dict[str, Any]:
    labels = sorted(
        {
            result["expected_intent"]
            for result in results
            if result.get("expected_intent") is not None
        }
        | {
            result["prediction"]["intent"]
            for result in results
            if result.get("prediction")
        }
    )
    total = len(results)
    per_label: dict[str, dict[str, float | int]] = {}
    for label in labels:
        true_positive = sum(
            1
            for result in results
            if result.get("expected_intent") == label
            and result["prediction"]["intent"] == label
        )
        false_positive = sum(
            1
            for result in results
            if result.get("expected_intent") != label
            and result["prediction"]["intent"] == label
        )
        false_negative = sum(
            1
            for result in results
            if result.get("expected_intent") == label
            and result["prediction"]["intent"] != label
        )
        precision, recall, f1 = _precision_recall_f1(
            true_positive,
            false_positive,
            false_negative,
        )
        support = sum(1 for result in results if result.get("expected_intent") == label)
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }

    macro = {
        key: _mean(float(metrics[key]) for metrics in per_label.values())
        for key in ("precision", "recall", "f1")
    }
    weighted = {
        key: _ratio(
            sum(float(metrics[key]) * int(metrics["support"]) for metrics in per_label.values()),
            total,
        )
        for key in ("precision", "recall", "f1")
    }
    return {
        "macro": macro,
        "weighted": weighted,
        "per_label": per_label,
    }


def _entity_precision_recall_f1(results: list[dict[str, Any]]) -> dict[str, float | int]:
    true_positive = 0
    false_positive = 0
    false_negative = 0

    for result in results:
        expected = _entity_counter(result.get("expected_entities", []))
        predicted = _entity_counter(result["prediction"].get("entities", []))
        for entity in set(expected) | set(predicted):
            true_positive += min(expected[entity], predicted[entity])
            false_positive += max(predicted[entity] - expected[entity], 0)
            false_negative += max(expected[entity] - predicted[entity], 0)

    precision, recall, f1 = _precision_recall_f1(true_positive, false_positive, false_negative)
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }


def _entity_signature(entities: list[dict[str, Any]]) -> list[tuple[str, str]]:
    return sorted((str(entity["entity_type"]), str(entity["value"])) for entity in entities)


def _entity_counter(entities: list[dict[str, Any]]) -> Counter[tuple[str, str]]:
    return Counter((str(entity["entity_type"]), str(entity["value"])) for entity in entities)


def _precision_recall_f1(
    true_positive: int,
    false_positive: int,
    false_negative: int,
) -> tuple[float, float, float]:
    precision = _ratio(true_positive, true_positive + false_positive) or 0.0
    recall = _ratio(true_positive, true_positive + false_negative) or 0.0
    f1 = _ratio(2 * precision * recall, precision + recall) or 0.0
    return precision, recall, f1


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _mean(values: Sequence[float] | Any) -> float | None:
    collected = list(values)
    if not collected:
        return None
    return sum(collected) / len(collected)


def write_or_print_json(payload: dict[str, Any], output_file: Path | None) -> None:
    if output_file is None:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
        file.write("\n")


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict intent and entities for one query.")
    parser.add_argument(
        "--model-family",
        choices=("bert", "roberta"),
        default="bert",
        help="Trained model family to load.",
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", help="User query to analyze.")
    input_group.add_argument(
        "--input-file",
        type=resolve_project_path,
        help=(
            "JSON list of queries, or an object with a queries list, for batch prediction. "
            "Each item may include expected_intent and expected_entities."
        ),
    )
    parser.add_argument(
        "--models-dir",
        type=resolve_project_path,
        default=DEFAULT_MODELS_DIR,
        help="Directory containing trained NLU model artifacts.",
    )
    parser.add_argument(
        "--config",
        type=resolve_project_path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to NLU training config JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=resolve_project_path,
        default=None,
        help=(
            "Append each prediction to <output-dir>/<model-family>.jsonl "
            f"(default when omitted: stdout only; suggested: {DEFAULT_PREDICTION_OUTPUT_DIR.name}/)."
        ),
    )
    parser.add_argument(
        "--output-file",
        type=resolve_project_path,
        default=None,
        help="Write the prediction payload as pretty JSON instead of printing it to stdout.",
    )
    parser.add_argument(
        "--run-id",
        default="",
        help="Optional label stored with the JSONL record to group battery runs.",
    )
    return parser.parse_args(argv)


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
