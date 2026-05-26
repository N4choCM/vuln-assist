# Response Generator (`services/response_generator`)

Phase 5 module that turns Phase 4 `retrieval` payloads into natural-language replies using grounded generation (RAG-lite: structured context, no vector DB).

## Responsibilities

- Serialize `retrieval` JSON into LLM context (`context_builder.py`).
- Build strict grounded prompts (`prompts.py`).
- Call Ollama when enabled (`generator.py` via `integrations/llm`).
- Fall back to deterministic templates when LLM is disabled or unavailable (`fallback.py`).

This package **never** exposes HTTP routes, performs NLU, or fetches NVD/MITRE data directly.

## Files

| File | Role |
|------|------|
| `config.py` | Loads `config/response_generator.json` + env overrides. |
| `context_builder.py` | Formats CVE + MITRE records for the prompt. |
| `prompts.py` | System and user prompt templates. |
| `fallback.py` | Deterministic replies (former `_format_retrieval_reply`). |
| `generator.py` | `ResponseGenerator.generate(user_query, intent, retrieval)`. |

## Usage

```python
from services.response_generator import ResponseGenerator

generator = ResponseGenerator()
reply = generator.generate(
    "What is CVE-2021-44228?",
    "CVE_LOOKUP",
    retrieval_dict,
)
```

## Configuration

Environment variables (see [`.env.example`](../../.env.example)):

| Variable | Default | Description |
|----------|---------|-------------|
| `RESPONSE_GENERATOR_ENABLED` | `false` | Enable Ollama generation |
| `LLM_PROVIDER` | `ollama` | `ollama` or `none` |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Local Ollama API |
| `OLLAMA_MODEL` | `llama3.2` | Model tag (`ollama pull llama3.2`) |

JSON defaults: [`config/response_generator.json`](../../config/response_generator.json).

## Backend integration

[`backend/repositories/response_generator_repository.py`](../../backend/repositories/response_generator_repository.py) wraps this module. [`backend/services/dialogue_app_service.py`](../../backend/services/dialogue_app_service.py) calls it after `ExternalDataRepository.fetch()`.

## Testing

```bash
pytest tests/test_response_generator.py
```

Manual E2E: [GUIA_PRUEBAS.md](../../GUIA_PRUEBAS.md) — Fase 5.
