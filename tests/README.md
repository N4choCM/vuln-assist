# Tests

This directory contains automated tests for the project.

## Current Coverage

The Phase 3 additions cover deterministic `DialogueEngine` transitions (`tests/test_dialogue_manager_engine.py`) and layered FastAPI smoke tests driven by mocked NLU stubs (`tests/test_backend_api_dialogue.py`).

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
