# Deployment

How to run VulnAssist as a **single web app** using Docker Compose: the chat UI, the API, and Ollama (for natural-language replies) start together.

The user opens **one URL**. Nginx serves the React frontend and forwards API requests to the backend. Ollama stays **inside Docker** — it is not exposed to the internet.

## What runs


| Service         | Role                                           |
| --------------- | ---------------------------------------------- |
| **frontend**    | Web interface (React + nginx)                  |
| **backend**     | API: NLU, dialogue, NVD, response generation   |
| **ollama**      | Local LLM for chat replies                     |
| **ollama-init** | Downloads the model on first start, then exits |


```text
Browser → frontend (port 8080 by default)
            → backend → Ollama (internal)
                     → NVD API
                     → NLU models + knowledge base (mounted from the repo)
```

## Before you start

- **Docker** with Compose
- **8 GB RAM** and ~20 GB disk (NLU + Ollama model)
- **Trained NLU models** in `models/nlu/` (not in git — train locally if missing):

```bash
python scripts/build_dataset.py
python scripts/train_nlu.py --model-family roberta
```

- Copy `.env` from the example: `cp .env.example .env`
- Optional: set `NVD_API_KEY` in `.env` for faster vulnerability lookups

## Run locally

From the **repository root**:

```bash
cp .env.example .env
docker compose -f deploy/docker-compose.yml up --build
```

Open [http://localhost:8080](http://localhost:8080). The first run may take a few minutes while Ollama downloads `llama3.2`.

Quick check: open the chat and ask e.g. *What is CVE-2021-44228?* — you should get a natural-language answer if `RESPONSE_GENERATOR_ENABLED=true` in `.env`.

## Main files


| File                                                         | Purpose                         |
| ------------------------------------------------------------ | ------------------------------- |
| [docker-compose.yml](docker-compose.yml)                     | Starts all services             |
| [Dockerfile.api](Dockerfile.api)                             | Backend image                   |
| [Dockerfile.web](Dockerfile.web)                             | Frontend build + nginx          |
| [nginx.conf](nginx.conf)                                     | Serves UI and proxies API       |
| [scripts/pull-ollama-model.sh](scripts/pull-ollama-model.sh) | Pulls Ollama model on first run |


Environment variables: see `[.env.example](../.env.example)`.

## Limitations (demo scope)

- Conversations are **in memory** — restarting the backend clears sessions.
- **No login** — intended for controlled demos, not public production.

## Related docs

- [frontend/README.md](../frontend/README.md) — UI development
- [backend/README.md](../backend/README.md) — API details

