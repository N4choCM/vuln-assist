"""Wrap the Phase 2 `NLUPipeline` so HTTP layers avoid Torch imports."""

from __future__ import annotations

from typing import Protocol

from services.nlu.models import NLUResult
from services.nlu.pipeline import NLUPipeline


class NLUPredictor(Protocol):
    """Structural typing hook for mocking predictions in isolated tests."""

    def predict(self, text: str) -> NLUResult:
        ...


class NLURepository:
    """Deterministic façade over trained HuggingFace checkpoints."""

    def __init__(self, pipeline: NLUPipeline) -> None:
        self._pipeline = pipeline

    def predict(self, text: str) -> NLUResult:
        return self._pipeline.predict(text)
