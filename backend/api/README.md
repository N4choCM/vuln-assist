# Backend API Wiring (`backend/api/`)

Responsible for creating the FastAPI instance, attaching lifespan hooks that provision `DialogueApplicationService`, and mounting routers exported from [`../controllers/`](../controllers/README.md).

## Files

| File | Role |
|------|------|
| `main.py` | Public `create_app()` factory plus default `app` object referenced by uvicorn (`backend.api.main:app`). Avoid adding business orchestration logic here beyond router registration + lifespan delegation. |
| `container.py` | Composes Torch-backed repositories and the deterministic dialogue engine (`DialogueEngine`) for runtime environments. Tests typically bypass this file by injecting a fake orchestration façade through `create_app(dialogue_application_service=...)`. |

## Lifespan Behaviour

Production mode (`create_app()` without overrides) invokes `container.build_production_dialogue_application_service()` once per worker process—**Transformer weights stay lazy-loaded** inside `services.nlu.NLUPipeline` until the first inference call hits the repository façade.
