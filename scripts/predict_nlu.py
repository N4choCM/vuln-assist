#!/usr/bin/env python3
"""Run prediction with a trained Phase 2 NLU model."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.nlu import NLUPipeline
from services.nlu.config import DEFAULT_CONFIG_PATH, DEFAULT_MODELS_DIR


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    pipeline = NLUPipeline(
        model_family=args.model_family,
        models_dir=args.models_dir,
        config_path=args.config,
    )
    result = pipeline.predict(args.text)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict intent and entities for one query.")
    parser.add_argument(
        "--model-family",
        choices=("bert", "roberta"),
        default="bert",
        help="Trained model family to load.",
    )
    parser.add_argument("--text", required=True, help="User query to analyze.")
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
    return parser.parse_args(argv)


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
