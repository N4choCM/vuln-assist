"""Configuration loading for NLU training and inference."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "nlu_training.json"
DEFAULT_DATASET_DIR = PROJECT_ROOT / "data" / "dataset" / "output"
DEFAULT_MODELS_DIR = PROJECT_ROOT / "models" / "nlu"


@dataclass(frozen=True)
class NLUTrainingConfig:
    """Runtime settings shared by BERT and RoBERTa training."""

    models: dict[str, str]
    learning_rate: float
    batch_size: int
    max_length: int
    early_stopping_patience: int
    seed: int
    num_train_epochs: int

    def model_name(self, model_family: str) -> str:
        try:
            return self.models[model_family]
        except KeyError as exc:
            available = ", ".join(sorted(self.models))
            raise ValueError(
                f"Unknown model family {model_family!r}. Available: {available}"
            ) from exc


def load_training_config(path: Path = DEFAULT_CONFIG_PATH) -> NLUTrainingConfig:
    """Load JSON config and keep defaults explicit for first-time setup."""

    payload = _read_json(path)
    return NLUTrainingConfig(
        models=dict(payload.get("models", {})),
        learning_rate=float(payload.get("learning_rate", 2e-5)),
        batch_size=int(payload.get("batch_size", 16)),
        max_length=int(payload.get("max_length", 96)),
        early_stopping_patience=int(payload.get("early_stopping_patience", 2)),
        seed=int(payload.get("seed", 42)),
        num_train_epochs=int(payload.get("num_train_epochs", 3)),
    )


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
