# Frontend (`frontend/`)

React 19 presentation layer for VulnAssist. This folder contains **UI only** — no NLU, dialogue, or external API logic.

## Responsibilities

- Capture user queries and display assistant replies.
- Persist `session_id` across turns for multi-turn dialogue.
- Optionally show pipeline metadata (intent, slots, retrieval summary) for demos and thesis evaluation.

## Stack

- React 19 + TypeScript
- Vite 6 (dev server on port 5173)
- Plain CSS (no UI framework)

## Prerequisites

- Node.js 18+ and npm
- Backend running on `http://localhost:8000` (see [backend/README.md](../backend/README.md))

## Quick start

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

In a second terminal, start the API:

```bash
NLU_MODEL_FAMILY=bert uvicorn backend.api.main:app --reload
```

## API integration

The UI calls a single endpoint:

```http
POST /v1/dialogue/message
{ "text": "...", "session_id": "..." | null }
```

During development, Vite proxies `/v1` and `/health` to `localhost:8000` (see [vite.config.ts](vite.config.ts)), so no CORS configuration is required locally.

For production or split origins, set:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

and configure CORS on the FastAPI app.

## Project layout

| Path | Role |
|------|------|
| [src/App.tsx](src/App.tsx) | Chat state, session handling, welcome examples |
| [src/api/dialogue.ts](src/api/dialogue.ts) | HTTP client for `/v1/dialogue/message` |
| [src/types/dialogue.ts](src/types/dialogue.ts) | TypeScript mirrors of API payloads |
| [src/components/](src/components/) | Chat window, bubbles, input |
| [src/styles/app.css](src/styles/app.css) | Layout and theme |

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Development server with hot reload |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview production build |

## Architecture boundary

The frontend must **not**:

- Classify intents or extract entities.
- Call NVD, MITRE, or Ollama directly.
- Duplicate business logic from `services/` or `backend/`.

All processing stays on the backend per [`.cursor/rules/architecture.mdc`](../.cursor/rules/architecture.mdc).

## Manual testing

See [GUIA_PRUEBAS.md](../GUIA_PRUEBAS.md) — Fase 6 checklist.
