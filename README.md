# Cybersecurity Vulnerability Conversational System

This project implements a hybrid NLP-based conversational system for cybersecurity vulnerability analysis.

The current repository covers:

- Phase 1: Data & Knowledge Layer.
- Phase 2: NLU Pipeline with BERT and RoBERTa intent classification plus BIO NER.
- Phase 3: Backend core (FastAPI orchestration via controllers → application services → repositories) and deterministic `DialogueEngine` finite-state dialogue policy.

The architecture follows the Cursor rules in `.cursor/rules/`: modules are separated by responsibility, and no API, NLP, integration, dataset, or response-generation logic is mixed across layers.

## Current Scope

Implemented:

- NVD integration client.
- CVE knowledge-base normalization and persistence.
- Template-based dataset generation.
- Real entity injection from the knowledge base.
- Rule-based paraphrasing.
- BIO annotation.
- Train/validation/test splitting.
- Dataset validation and output writing.
- HuggingFace-based NLU training for BERT and RoBERTa.
- Intent classification evaluation.
- BIO NER evaluation.
- Runtime `NLUPipeline` prediction interface.
- FastAPI layered API (`controllers` / `backend/services` / `repositories`) with `POST /v1/dialogue/message`.
- Dialogue manager finite-state workflow (`services/dialogue_manager`) emitting templated replies and slot-tracking for future query execution.

Not implemented yet:

- Frontend layer.
- Query builder.
- Response generation.
- MITRE integration.
- Deployment.

## Project Structure

```text
.
├── .cursor/
│   └── rules/
├── README.md
├── INFORME_PROYECTO.md
├── config/
├── context/
├── data/
│   ├── knowledge_base/
│   └── dataset/
├── integrations/
│   └── nvd/
├── models/
│   └── nlu/
├── backend/
├── scripts/
├── services/
│   ├── nlu/
│   └── dialogue_manager/
└── tests/
```

## Important Directories

- [config/](config/README.md): project configuration files.
- [integrations/](integrations/README.md): external data-source integrations.
- [integrations/nvd/](integrations/nvd/README.md): NVD CVE API client.
- [data/](data/README.md): project data layer.
- [data/knowledge_base/](data/knowledge_base/README.md): normalized CVE records.
- [data/dataset/](data/dataset/README.md): NLU dataset generation.
- [data/dataset/pipeline/](data/dataset/pipeline/README.md): dataset builder, splitter, validator, and writer.
- [data/dataset/output/](data/dataset/output/README.md): generated dataset artifacts.
- [services/](services/README.md): core service-layer modules.
- [services/nlu/](services/nlu/README.md): Phase 2 NLU training and prediction.
- [services/dialogue_manager/](services/dialogue_manager/README.md): Phase 3 dialogue FSM.
- [backend/](backend/README.md): Phase 3 FastAPI orchestration (controllers, repos, adapters).
- [models/](models/README.md): local trained model artifacts.
- [models/nlu/](models/nlu/README.md): NLU model output directory.
- [scripts/](scripts/README.md): executable entry points.
- [tests/](tests/README.md): automated tests.
- [context/](context/README.md): project documentation/context files.

## Quick Start

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Generate the Phase 1 dataset:

```bash
python3 scripts/build_dataset.py
```

For a larger NLU training dataset:

```bash
python3 scripts/build_dataset.py --samples 1000
```

Train one Phase 2 model family:

```bash
python3 scripts/train_nlu.py --model-family bert
python3 scripts/train_nlu.py --model-family roberta
```

Run prediction after training:

```bash
python3 scripts/predict_nlu.py --model-family bert --text "What is CVE-2021-44228?"
```

Run the Phase 3 dialogue API locally (Torch models lazy-load when the repository first invokes `predict`):

```bash
NLU_MODEL_FAMILY=bert uvicorn backend.api.main:app --reload
```

Then probe `GET /health` or call `POST /v1/dialogue/message` (`session_id` optional; one is minted automatically).

## Generated Outputs

Phase 1 writes:

```text
data/dataset/output/intents.json
data/dataset/output/ner.conll
```

Phase 2 writes local model artifacts and metrics:

```text
models/nlu/bert/
models/nlu/roberta/
models/nlu/evaluation_summary.json
```

Trained models are ignored by git because they are generated local artifacts.

## Data Flow

Phase 1:

```text
scripts/build_dataset.py
    -> data/knowledge_base
    -> data/dataset/pipeline
    -> data/dataset/output
```

Phase 2:

```text
data/dataset/output
    -> services/nlu
    -> models/nlu
```

Phase 3 (HTTP):

```text
client HTTP
    -> backend/controllers (FastAPI)
        -> backend/services (dialogue application service)
        -> backend/repositories (+ services/nlu NLUPipeline, services/dialogue_manager DialogueEngine)
```

Future full-system flow:

```text
User -> API -> NLU -> Dialogue Manager -> Query Builder -> External APIs -> Response Generator -> API -> User
```

## Useful Checks

```bash
python3 scripts/build_dataset.py
python3 -m compileall integrations data services backend scripts
pytest
```

Training BERT and RoBERTa requires the dependencies in `requirements.txt` and internet access the first time HuggingFace models are downloaded.

## Architecture Boundary

The project must remain modular:

- External API access belongs in `integrations/`.
- Normalized data belongs in `data/knowledge_base/`.
- Dataset generation belongs in `data/dataset/`.
- Core NLU logic belongs in `services/nlu/`.
- Dialogue finite-state orchestration belongs in `services/dialogue_manager/`.
- Executable orchestration belongs in `scripts/`.
- Generated model artifacts belong in `models/`.
- HTTP adapters (FastAPI routers) live in [`backend/`](backend/README.md); they must orchestrate domain packages without importing Torch inside controllers.

Frontend, query builder, and response generation modules should continue following `.cursor/rules/architecture.mdc` once they ship.

## Maintenance Conventions

- Every folder must contain a `README.md`.
- Parent README files should link to child README files.
- When code is created, modified, or removed, update the README in that folder if behavior, usage, purpose, or file lists change.
- Update parent README files when a change affects parent-level understanding.
- Code should include concise comments for non-obvious blocks such as regex, retries, validation, transformations, pagination, BIO tagging, token alignment, and architecture boundaries.
