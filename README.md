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

## Project Structure (summary)

```text
.
├── README.md
├── config/
├── context/
├── data/
│   ├── knowledge_base/
│   ├── dataset/
│   └── evaluation/
├── docs/
├── integrations/
│   ├── nvd/
│   ├── mitre/
│   └── llm/
├── models/
│   └── nlu/
├── backend/
├── deploy/
├── frontend/
├── results/
├── scripts/
├── services/
│   ├── nlu/
│   ├── dialogue_manager/
│   ├── query_builder/
│   └── response_generator/
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

## Quick Start

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Generate the dataset:

```bash
python scripts/build_dataset.py --samples 1000
```

Train one model family:

```bash
python scripts/train_nlu.py --model-family bert
python scripts/train_nlu.py --model-family roberta
```

Run prediction after training for each model:

```bash
python scripts/predict_nlu.py \
  --model-family bert \
  --input-file data/evaluation/nlu_manual_queries.json \
  --output-file results/nlu_predictions/bert.json \
  --run-id nlu_manual_120_20260606
```

```bash
python scripts/predict_nlu.py \
  --model-family roberta \
  --input-file data/evaluation/nlu_manual_queries.json \
  --output-file results/nlu_predictions/roberta.json \
  --run-id nlu_manual_120_20260606
```

Run the dialogue API locally (you can select the model you prefer, but, as stated in the dissertation, roberta performs slightly better):

```bash
NLU_MODEL_FAMILY=roberta uvicorn backend.api.main:app --reload
```

Then probe `GET /health` or call `POST /v1/dialogue/message` (`session_id` optional; one is minted automatically).

Run the frontend locally (requires Node.js 18+):

```bash
cd frontend && npm install && npm run dev
```

With the API on port 8000, open [http://localhost:5173](http://localhost:5173).

Run the full stack app locally in a Docker container (requires trained NLU checkpoints and Docker):

```bash
cp .env.example .env # Add your NVD API KEY if you want faster responses
docker compose -f deploy/docker-compose.yml up --build
```

Open [http://localhost:8080](http://localhost:8080). See [deploy/README.md](deploy/README.md) for VPS deployment.

## Generated Outputs

The dataset generation pipeline writes:

```text
data/dataset/output/intents.json
data/dataset/output/ner.conll
```

The NLU pipeline writes local model artifacts and metrics:

```text
models/nlu/bert/
models/nlu/roberta/
models/nlu/evaluation_summary.json
```

