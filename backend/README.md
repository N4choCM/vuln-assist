# Backend (`backend/`)

Phase 3 exposes the conversational stack through FastAPI **without embedding NLP inside routers**.
This package follows a classic layering model:

```
controllers → backend/services → repositories → core services under ../services/
```

## Layout

```text
backend/
├── README.md                     ← this file
├── api/
│   ├── main.py                   # Thin ASGI bootstrap + lifespan wiring
│   └── container.py              # Builds default production services
├── controllers/
│   ├── dialogue.py               # POST /v1/dialogue/message
│   └── health.py                 # GET /health readiness helper
├── services/
│   └── dialogue_app_service.py   # Use-case façade orchestrating repos + NLU + FSM
├── repositories/
│   ├── session_repository.py     # Thread-safe in-memory sessions (swap later)
│   └── nlu_repository.py         # Wraps Phase 2 NLUPredictor
└── schemas/
    └── dialogue.py               # Pydantic payloads returned to callers
```

Naming reminder: **`backend/services/` hosts HTTP orchestration** while [`../services/`](../services/README.md) retains **domain modules** (`nlu`, `dialogue_manager`, future `query_builder`).

## Authentication

Production-style auth (JWT, API keys, user accounts) intentionally stays **out-of-scope for Phase 3**.
Deploy behind perimeter controls until a later milestone adds explicit authentication.

## Run locally

```bash
python3 -m pip install -r requirements.txt  # installs FastAPI + uvicorn extras
NLU_MODEL_FAMILY=bert uvicorn backend.api.main:app --reload
```

`GET /health` reports whether checkpoints exist under `models/nlu/<family>/`; models still lazy-load inside `services.nlu.NLUPipeline`.

## Useful checks

```bash
python3 -m compileall backend services
pytest tests/test_backend_api_dialogue.py tests/test_dialogue_manager_engine.py
```

## References

- [backend/api/README.md](api/README.md) — lifespan + factory details.
- [services/dialogue_manager/README.md](../services/dialogue_manager/README.md) — FSM internals (no FastAPI coupling).
