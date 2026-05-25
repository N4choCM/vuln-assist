# HTTP Controllers (`backend/controllers/`)

FastAPI routers that stay intentionally thin:

- Deserialize Pydantic models from [`backend/schemas/`](../schemas/README.md).
- Resolve dependencies injected through FastAPI (`Depends`).
- Immediately delegate persistence + policy decisions to [`backend/services/`](../services/README.md).

Torch, Transformers, and dataset loaders never appear in this layer.
