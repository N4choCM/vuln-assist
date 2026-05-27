# Cybersecurity Vulnerability Conversational System

Hybrid NLP-based conversational system for cybersecurity vulnerability analysis (VulnAssist).

The current repository covers:

- Phase 1: Data & Knowledge Layer.
- Phase 2: NLU Pipeline with BERT and RoBERTa intent classification plus BIO NER.
- Phase 3: Backend core (FastAPI orchestration via controllers → application services → repositories) and deterministic `DialogueEngine` finite-state dialogue policy.
- Phase 4: Query Builder, live NVD retrieval, and MITRE ATT&CK local index enrichment.
- Phase 5: Grounded response generation via Ollama (RAG-lite from structured `retrieval` context).
- Phase 6: React chat UI consuming `POST /v1/dialogue/message`.
- Phase 8: VPS deployment via Docker Compose (nginx + API + Ollama, single public URL).

The architecture follows the Cursor rules in `.cursor/rules/`: modules are separated by responsibility, and no API, NLP, integration, dataset, or response-generation logic is mixed across layers.

## Testing Guide

Step-by-step instructions for Phases 1–8 (automated tests, manual checks, and E2E API):

- **[GUIA_PRUEBAS.md](GUIA_PRUEBAS.md)** — guía de pruebas por fase (español).
- **[MEMORIA_IDEAS_POR_FASE.md](MEMORIA_IDEAS_POR_FASE.md)** — ideas de contenido para la memoria del TFG por fase (español).

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
- Dialogue manager finite-state workflow (`services/dialogue_manager`) emitting templated replies and slot-tracking for query execution.
- Query Builder intent/slot → NVD query mapping (`services/query_builder`).
- Live NVD retrieval via external data repository.
- MITRE ATT&CK local index lookup and enrichment (`integrations/mitre`).
- Grounded LLM response generation (`services/response_generator`) with Ollama and deterministic fallback.
- React chat frontend (`frontend/`) with multi-turn session handling and optional technical details panel.
- Docker Compose deployment (`deploy/`) — nginx same-origin proxy, FastAPI, internal Ollama for public VPS demos.

Not implemented yet:

- Extended system evaluation — Phase 7.

See [GUIA_PRUEBAS.md](GUIA_PRUEBAS.md) for how to validate each implemented phase.

## Project Structure (summary)

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
├── deploy/
├── frontend/
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
- [services/query_builder/](services/query_builder/README.md): Phase 4 query mapping.
- [services/response_generator/](services/response_generator/README.md): Phase 5 LLM replies.
- [integrations/llm/](integrations/llm/README.md): Ollama HTTP client.
- [backend/](backend/README.md): Phase 3 FastAPI orchestration (controllers, repos, adapters).
- [frontend/](frontend/README.md): Phase 6 React chat UI (presentation only).
- [deploy/](deploy/README.md): Phase 8 Docker Compose VPS stack.
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

Run the Phase 6 frontend (requires Node.js 18+):

```bash
cd frontend && npm install && npm run dev
```

With the API on port 8000, open [http://localhost:5173](http://localhost:5173).

Run the Phase 8 full stack locally (requires trained NLU checkpoints and Docker):

```bash
cp .env.example .env
docker compose -f deploy/docker-compose.yml up --build
```

Open [http://localhost:8080](http://localhost:8080). See [deploy/README.md](deploy/README.md) for VPS deployment.

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

Phase 4 extends the repository layer with `services/query_builder` and live calls to `integrations/nvd` and `integrations/mitre`.

Phase 5 adds `services/response_generator` and optional Ollama calls through `integrations/llm`.

Phase 6 (browser):

```text
User -> frontend/ (React)
    -> backend/controllers POST /v1/dialogue/message
        -> (full pipeline as above)
    -> reply displayed in chat UI
```

Phase 8 (Docker VPS):

```text
User -> deploy/frontend (nginx + React)
    -> /v1 -> backend (FastAPI) -> ... -> ollama (internal)
    -> reply displayed in chat UI
```

Full-system flow:

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

Additional documentation:

- [GUIA_PRUEBAS.md](GUIA_PRUEBAS.md): how to test Phases 1–8 (Spanish).
- [deploy/README.md](deploy/README.md): Docker Compose VPS deployment (Phase 8).
- [MEMORIA_IDEAS_POR_FASE.md](MEMORIA_IDEAS_POR_FASE.md): thesis memory content ideas per phase (Spanish).
- [INFORME_PROYECTO.md](INFORME_PROYECTO.md): detailed Spanish report explaining folders, files, local testing, execution flow, and Mermaid diagrams.
- [context/DATASET_PIPELINE_FLOW.md](context/DATASET_PIPELINE_FLOW.md): beginner-friendly Spanish explanation of the dataset generation flow.

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

Frontend must remain presentation-only per `.cursor/rules/architecture.mdc`; query builder and response generation live in `services/`.

## Maintenance Conventions

- Every folder must contain a `README.md`.
- Parent README files should link to child README files.
- When code is created, modified, or removed, update the README in that folder if behavior, usage, purpose, or file lists change.
- Update parent README files when a change affects parent-level understanding.
- Code should include concise comments for non-obvious blocks such as regex, retries, validation, transformations, pagination, BIO tagging, token alignment, and architecture boundaries.
