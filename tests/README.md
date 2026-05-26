# Tests

This directory contains automated tests for the project.

## Current Coverage

The Phase 3 additions cover deterministic `DialogueEngine` transitions (`tests/test_dialogue_manager_engine.py`) and layered FastAPI smoke tests driven by mocked NLU stubs (`tests/test_backend_api_dialogue.py`).

Phase 4 tests cover query-builder mapping and external data retrieval (`tests/test_query_builder.py`, `tests/test_external_data_repository.py`).

Phase 5 tests cover context building, fallback replies, and mocked LLM generation (`tests/test_response_generator.py`). `conftest.py` sets `RESPONSE_GENERATOR_ENABLED=false` so pytest does not require Ollama.

Per-phase manual and E2E instructions: [GUIA_PRUEBAS.md](../GUIA_PRUEBAS.md).

The Phase 2 tests cover:

- Intent dataset loading.
- CoNLL BIO NER dataset loading.
- BIO label generation from shared entity labels.
- Subword label alignment for NER training.
- Accuracy, Precision, Recall, and F1 metrics.
- Public `NLUPipeline.predict()` result shape with model calls mocked.
- Runtime NER tokenization and subword-to-entity reconstruction.
- Dataset sample-size validation limits.

## Running Tests

From the project root:

```bash
pytest
```

## Boundary

FastAPI regressions instantiate `starlette.testclient.TestClient` as a context manager so lifespan hooks hydrate `dialogue_application_service` before invoking routers (`with TestClient(app) as client:`).

Mocks may monkeypatch heavyweight inference; suites should skip downloading checkpoints unless executing explicit integration notebooks.
