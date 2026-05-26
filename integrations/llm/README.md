# LLM Integration (`integrations/llm`)

HTTP client for external LLM providers used by Phase 5 response generation.

## Scope

This layer handles **only** outbound LLM API calls. It does not build prompts, format retrieval context, or generate business logic—that belongs in [`services/response_generator/`](../../services/response_generator/README.md).

## Current provider

- **Ollama** (local, no API key): `OllamaClient` posts to `/api/chat`.

## Usage

```python
from integrations.llm import OllamaClient, OllamaConfig

client = OllamaClient(
    OllamaConfig(
        base_url="http://127.0.0.1:11434",
        model="llama3.2",
        temperature=0.1,
        max_tokens=300,
        timeout_seconds=30.0,
    )
)
text = client.complete(system="You are helpful.", user="Summarize CVE-2021-44228.")
```

## Prerequisites

```bash
# Install Ollama from https://ollama.com, then:
ollama pull llama3.2
ollama serve   # usually starts automatically
```

## Files

| File | Role |
|------|------|
| `client.py` | `LLMClient` protocol, `OllamaClient`, `OllamaConfig`. |
