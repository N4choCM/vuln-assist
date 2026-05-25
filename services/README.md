# Services Layer

This directory contains core system logic.

Services must remain independent from the API, frontend, and external integration layers. They may consume structured data from `data/` and return structured results to future orchestration layers.

## Subdirectories

- [nlu/](nlu/README.md): Phase 2 Natural Language Understanding module.
- [dialogue_manager/](dialogue_manager/README.md): Phase 3 conversational finite-state policy (`DialogueEngine`).


## Boundary

This layer may contain:

- NLU logic.
- Dialogue manager FSM/policy logic (`services/dialogue_manager`).
- Future query-builder logic.
- Future response-generation logic.

This layer must not:

- Define FastAPI routes.
- Render frontend UI.
- Fetch external APIs directly.
- Generate the Phase 1 dataset.
