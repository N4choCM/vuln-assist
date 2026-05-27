# Deployment (Phase 8)

Docker Compose stack for a **public demo on a VPS** with a single URL: nginx serves the React UI and reverse-proxies `/v1` and `/health` to FastAPI. Ollama runs on the internal Docker network only (not exposed to the internet).

## Architecture

```text
Browser → frontend:80 (nginx + React dist)
              ├─ /        → static files
              ├─ /v1/*    → backend:8000
              └─ /health  → backend:8000

backend → ollama:11434 (LLM, internal)
backend → NVD API (live)
backend → models/nlu/ (volume)
backend → data/knowledge_base/ (volume)
```

## Prerequisites

| Requirement | Notes |
|-------------|--------|
| Docker + Compose plugin | v2 recommended |
| **≥ 8 GB RAM** on the host | PyTorch NLU + Ollama (`llama3.2`) |
| ~20 GB disk | NLU checkpoints + Ollama model cache |
| NLU checkpoints | `models/nlu/bert/intent/` and `models/nlu/bert/ner/` (train locally; not in git) |
| Knowledge base | `data/knowledge_base/` (shipped in repo) |

Train models if missing:

```bash
python3 scripts/build_dataset.py
python3 scripts/train_nlu.py --model-family bert
```

## Local smoke test

From the **repository root**:

```bash
cp .env.example .env
# Optional: set NVD_API_KEY in .env for faster NVD calls
docker compose -f deploy/docker-compose.yml up --build
```

First start downloads the Ollama model (can take several minutes). Open [http://localhost:8080](http://localhost:8080) (override with `WEB_PORT=80` on Linux VPS).

Docker Desktop shows the stack as project **`vuln-assist`** with containers `vuln-assist-frontend-1`, `vuln-assist-backend-1`, `vuln-assist-ollama-1`, and `vuln-assist-ollama-init-1` (init exits after model pull).

If you previously ran an older compose file (project `deploy`), remove the old stack first:

```bash
docker compose -f deploy/docker-compose.yml -p deploy down
```

Checks:

```bash
curl -s http://localhost:8080/health | python3 -m json.tool
curl -s -X POST http://localhost:8080/v1/dialogue/message \
  -H 'Content-Type: application/json' \
  -d '{"text":"What is CVE-2021-44228?"}' | python3 -m json.tool
```

Expect `status: ok` when checkpoints exist and a natural-language `reply` when Ollama is enabled.

## VPS deployment

### 1. Provision server

- Ubuntu 22.04+ (or similar)
- 8 GB+ RAM, public IP
- Install Docker: [https://docs.docker.com/engine/install/ubuntu/](https://docs.docker.com/engine/install/ubuntu/)

### 2. Copy project and models

NLU weights are gitignored — copy them explicitly:

```bash
rsync -avz --exclude node_modules --exclude .git \
  ./ user@YOUR_VPS:/opt/vulnassist/

rsync -avz models/nlu/ user@YOUR_VPS:/opt/vulnassist/models/nlu/
```

### 3. Configure environment

On the VPS:

```bash
cd /opt/vulnassist
cp .env.example .env
nano .env   # set NVD_API_KEY, verify OLLAMA_MODEL
```

### 4. Start stack

```bash
docker compose -f deploy/docker-compose.yml up --build -d
docker compose -f deploy/docker-compose.yml logs -f ollama-init   # first pull
```

Publish on port 80 (production):

```bash
WEB_PORT=80 docker compose -f deploy/docker-compose.yml up --build -d
```

Ensure firewall allows `80/tcp` (and `443` if you add TLS).

### 5. HTTPS (recommended)

**Option A — Caddy** (simplest): run Caddy on the host proxying to `localhost:8080`, automatic Let's Encrypt.

**Option B — Cloudflare**: DNS proxy in front of the VPS IP; origin HTTP on port 80.

**Option C — certbot + nginx** on the host in front of the compose `frontend` port.

Document the chosen method in your thesis; TLS termination stays outside this compose file by design.

### 6. Post-deploy checklist

- [ ] `GET https://your-domain/health` → `"status": "ok"`, `"models_ready": true`
- [ ] Chat UI loads at `/`
- [ ] CVE query returns LLM `reply` (not only a one-line fallback)
- [ ] Ollama has **no** public port (`docker compose ps` — only `frontend` publishes ports)
- [ ] `NVD_API_KEY` set for acceptable latency under demo load

## Files

| File | Purpose |
|------|---------|
| [Dockerfile.api](Dockerfile.api) | FastAPI + Torch runtime |
| [Dockerfile.web](Dockerfile.web) | Node build + nginx |
| [nginx.conf](nginx.conf) | Static SPA + API proxy |
| [docker-compose.yml](docker-compose.yml) | Project `vuln-assist`: `frontend`, `backend`, `ollama`, `ollama-init` |
| [scripts/pull-ollama-model.sh](scripts/pull-ollama-model.sh) | One-shot model pull |

## Environment variables

See [`.env.example`](../.env.example). Key values for compose:

| Variable | Compose default | Role |
|----------|-----------------|------|
| `RESPONSE_GENERATOR_ENABLED` | `true` | LLM replies |
| `OLLAMA_BASE_URL` | overridden to `http://ollama:11434` | Internal Ollama |
| `OLLAMA_MODEL` | `llama3.2` | Pulled by `ollama-init` |
| `NLU_MODEL_FAMILY` | `bert` | Checkpoint subdirectory |
| `NVD_API_KEY` | optional | Faster NVD API pace |
| `WEB_PORT` | `8080` | Host port mapped to nginx |

## Known limitations

- **Sessions** are in-memory ([`backend/repositories/session_repository.py`](../backend/repositories/session_repository.py)); use **one uvicorn worker**; restarts lose conversation state.
- **No authentication** — suitable for controlled demos; abuse can consume NVD/Ollama quota.
- **No NVD response cache** — mitigate with `NVD_API_KEY`.
- **Concurrent users** on a small VPS will queue on NLU + Ollama; plan demo load accordingly.

## Alternative hosting

Netlify/Vercel only serve static frontends; this project’s full pipeline (NLU + Ollama) requires the VPS stack above. A split deploy (static host + remote API) is possible later with CORS and `VITE_API_BASE_URL`, but is not the primary path for Phase 8.

## Related docs

- [GUIA_PRUEBAS.md](../GUIA_PRUEBAS.md) — Fase 8 validation checklist
- [frontend/README.md](../frontend/README.md) — UI development vs Docker deploy
- [backend/README.md](../backend/README.md) — API layer details
