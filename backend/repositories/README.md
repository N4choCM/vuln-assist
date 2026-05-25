# Backend Repositories (`backend/repositories/`)

Repository-style adapters bridging infrastructure concerns (`NLUPipeline`, future Redis stores) into the application services without leaking implementation details upwards.

## Current Implementations

| Module | Behaviour |
|--------|-----------|
| `session_repository.py` | Thread-safe in-memory dictionaries keyed by session UUID strings. Enough for demos + tests; Phase 8 deployments can subclass or replace with networked stores while keeping controllers untouched. |
| `nlu_repository.py` | Wraps Phase 2 `NLUPipeline` so FastAPI routers never directly import Torch modules. Implements the `NLUPredictor` Protocol for mocking in isolation tests. |
