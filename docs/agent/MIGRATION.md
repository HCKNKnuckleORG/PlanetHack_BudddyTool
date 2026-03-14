# PlanetHack – Go + Python + TypeScript Migration

This document describes the migration to a three-language stack: **Python** (API/engine), **TypeScript** (SPA frontend), and **Go** (performance layer).

## What Changed

### 1. Python REST API v1 (`/api/v1/*`)

- **`python/web/api_blueprint.py`** – New API blueprint with JSON-only endpoints
- **`python/web/jobs.py`** – Extracted job store for async recon/module execution
- **`python/web/app.py`** – Registers API blueprint, adds CORS for SPA
- All API routes return JSON. CORS enabled for cross-origin requests.

**API Endpoints:**
- `GET /api/v1/health` – Health check
- `GET /api/v1/quote` – Random movie quote
- `GET /api/v1/modules` – List bug bounty modules
- `POST /api/v1/recon/preflight` – Preflight check
- `POST /api/v1/recon/plan` – Build recon plan
- `POST /api/v1/recon/execute` – Execute phases (returns `job_id`)
- `POST /api/v1/recon/confirm/<job_id>` – Confirm/stop between phases
- `GET /api/v1/stream/<job_id>` – SSE stream of job output
- `GET /api/v1/findings/<job_id>` – Parsed findings
- `GET /api/v1/session/findings` – Cumulative session findings
- `POST /api/v1/modules/run` – Run a module
- `POST /api/v1/nextsteps/execute` – Run a next-step command

### 2. TypeScript SPA (`frontend/`)

- **Vite + React + TypeScript**
- Pages: Home, Recon, Modules, Terminal, Report History
- API client in `src/api/client.ts` – all calls go to `/api/v1` (proxied to Python)
- Cyber/Matrix theme consistent with legacy UI

**Run:**
```bash
# Terminal 1: Python API
python main.py --web

# Terminal 2: Vite dev server
cd frontend && npm install && npm run dev
# Open http://localhost:5173
```

Vite proxies `/api` to `http://localhost:8080`.

### 3. Other Updates

- **`.gitignore`** – Added `sessions/` to avoid committing scan data
- **`README.md`** – Updated structure, TypeScript SPA quick start

## Backward Compatibility

- **Legacy Flask UI** – Still available at `python main.py --web` (HTML templates)
- **Tkinter GUI** – Unchanged (`python main.py --gui`)
- **CLI** – Unchanged (`python main.py --cli`)
- **Recon flow** – Same phases; nmap handles port scanning

## Next Steps (Optional)

1. **Matrix rain** – Add canvas animation to TypeScript Home page
2. **Phase confirm** – Wire “continue/stop” between phases in SPA
3. **Docker** – Build frontend and serve from Flask in production
