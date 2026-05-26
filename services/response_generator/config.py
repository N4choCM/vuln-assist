"""Configuration for Phase 5 response generation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from integrations.llm.client import OllamaClient, OllamaConfig

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "response_generator.json"


@dataclass(frozen=True)
class ResponseGeneratorConfig:
    """Runtime settings for grounded LLM replies."""

    enabled: bool
    provider: str
    temperature: float
    max_tokens: int
    ollama_base_url: str
    ollama_model: str
    timeout_seconds: float


def load_response_generator_config(
    path: Path = DEFAULT_CONFIG_PATH,
) -> ResponseGeneratorConfig:
    """Load JSON defaults and apply environment overrides."""

    payload = _read_json(path)
    enabled = _env_bool("RESPONSE_GENERATOR_ENABLED", default=False)
    provider = os.environ.get("LLM_PROVIDER", "ollama").strip().lower()

    return ResponseGeneratorConfig(
        enabled=enabled,
        provider=provider,
        temperature=float(payload.get("temperature", 0.1)),
        max_tokens=int(payload.get("max_tokens", 300)),
        ollama_base_url=os.environ.get(
            "OLLAMA_BASE_URL",
            str(payload.get("ollama_base_url", "http://127.0.0.1:11434")),
        ),
        ollama_model=os.environ.get(
            "OLLAMA_MODEL",
            str(payload.get("ollama_model", "llama3.2")),
        ),
        timeout_seconds=float(
            os.environ.get(
                "OLLAMA_TIMEOUT_SECONDS",
                payload.get("timeout_seconds", 30),
            )
        ),
    )


def build_llm_client(config: ResponseGeneratorConfig) -> OllamaClient | None:
    """Instantiate an Ollama client when generation is enabled."""

    if not config.enabled or config.provider == "none":
        return None
    if config.provider != "ollama":
        raise ValueError(
            f"Unsupported LLM provider {config.provider!r}. Use 'ollama' or 'none'."
        )
    return OllamaClient(
        OllamaConfig(
            base_url=config.ollama_base_url,
            model=config.ollama_model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout_seconds=config.timeout_seconds,
        )
    )


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)
