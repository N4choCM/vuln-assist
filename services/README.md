# Services Layer

This directory contains core system logic.

Services must remain independent from the API, frontend, and external integration layers. They may consume structured data from `data/` and return structured results to future orchestration layers.

## Subdirectories

- [nlu/](nlu/README.md): Phase 2 Natural Language Understanding module.
- [dialogue_manager/](dialogue_manager/README.md): Phase 3 conversational finite-state policy (`DialogueEngine`).
- [query_builder/](query_builder/README.md): Phase 4 intent/slot → external API query mapping.
- [response_generator/](response_generator/README.md): Phase 5 grounded LLM reply generation.


## Boundary

This layer may contain:

- NLU logic.
- Dialogue manager FSM/policy logic (`services/dialogue_manager`).
- Query-builder logic (`services/query_builder`).
- Response-generation logic (`services/response_generator`).

This layer must not:

- Define FastAPI routes.
- Render frontend UI.
- Fetch external APIs directly.
- Generate the Phase 1 dataset.
