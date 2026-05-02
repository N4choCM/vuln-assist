"""Persistence for normalized CVE knowledge-base records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from data.knowledge_base.models import NormalizedCVE


class KnowledgeBaseRepository:
    """Read and write normalized CVE records as JSON."""

    def __init__(self, path: Path) -> None:
        # The repository owns one JSON file path for all load/save operations.
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._path.exists()

    def load(self) -> list[NormalizedCVE]:
        with self._path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        # The KB is stored as a top-level JSON array of CVE objects.
        if not isinstance(payload, list):
            raise ValueError(f"Knowledge base must be a JSON list: {self._path}")
        return [NormalizedCVE.from_mapping(item) for item in payload if isinstance(item, dict)]

    def save(self, records: Iterable[NormalizedCVE]) -> None:
        # Ensure the target directory exists before opening the JSON file for writing.
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [record.to_dict() for record in records]
        with self._path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, ensure_ascii=False)
            file.write("\n")
