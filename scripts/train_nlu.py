#!/usr/bin/env python3
"""Train NLU models."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.nlu import load_training_config, train_all, train_model_family
from services.nlu.config import DEFAULT_CONFIG_PATH, DEFAULT_DATASET_DIR, DEFAULT_MODELS_DIR


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    config = load_training_config(args.config)

    print("NLU training pipeline")
    print(f"- config: {args.config}")
    print(f"- intent dataset: {args.intents_path}")
    print(f"- NER dataset: {args.ner_path}")
    print(f"- output directory: {args.output_dir}")

    if args.model_family == "all":
        metrics = train_all(
            config=config,
            intents_path=args.intents_path,
            ner_path=args.ner_path,
            output_dir=args.output_dir,
        )
        print(f"- wrote summary: {args.output_dir / 'evaluation_summary.json'}")
        print(f"- trained families: {', '.join(metrics)}")
        return 0

    train_model_family(
        model_family=args.model_family,
        config=config,
        intents_path=args.intents_path,
        ner_path=args.ner_path,
        output_dir=args.output_dir,
    )
    print(f"- wrote metrics: {args.output_dir / args.model_family / 'metrics.json'}")
    print("NLU training completed successfully.")
    return 0


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train intent and NER NLU models.")
    parser.add_argument(
        "--model-family",
        choices=("all", "bert", "roberta"),
        default="all",
        help="Model family to train.",
    )
    parser.add_argument(
        "--config",
        type=resolve_project_path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to NLU training config JSON.",
    )
    parser.add_argument(
        "--intents-path",
        type=resolve_project_path,
        default=DEFAULT_DATASET_DIR / "intents.json",
        help="Path to intent dataset.",
    )
    parser.add_argument(
        "--ner-path",
        type=resolve_project_path,
        default=DEFAULT_DATASET_DIR / "ner.conll",
        help="Path to BIO NER dataset.",
    )
    parser.add_argument(
        "--output-dir",
        type=resolve_project_path,
        default=DEFAULT_MODELS_DIR,
        help="Directory for trained NLU model artifacts.",
    )
    return parser.parse_args(argv)


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
