"""Simple readiness probe without pulling heavy Torch models."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter

from services.nlu.config import DEFAULT_MODELS_DIR

router = APIRouter(tags=["health"])

_MODEL_FAMILY_ENV = "NLU_MODEL_FAMILY"


@router.get("/health")
def read_health() -> dict[str, object]:
    """Report whether checkpoints exist locally (lazy loading preserves startup speed)."""

    family = os.environ.get(_MODEL_FAMILY_ENV, "bert")
    checkpoints_root = Path(DEFAULT_MODELS_DIR) / family
    intent_ckpt = (checkpoints_root / "intent").exists()
    ner_ckpt = (checkpoints_root / "ner").exists()

    models_ready = intent_ckpt and ner_ckpt
    return {
        "status": "ok" if models_ready else "not_ready",
        "model_family": family,
        "models_ready": models_ready,
    }
