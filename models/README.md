# Models

This directory stores local trained model artifacts.

Model artifacts are generated outputs and are ignored by git unless a README is explicitly tracked.

## Subdirectories

- [nlu/](nlu/README.md): trained Phase 2 NLU models and metrics.

## Boundary

This directory should contain model outputs only. Training logic belongs in `services/nlu/`, and orchestration belongs in `scripts/`.
