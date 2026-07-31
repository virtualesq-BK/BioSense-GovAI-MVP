# BioSense-GovAI

AI-powered **biomarker–biosensor co-design** SaaS platform for early cancer detection using ctDNA molecular characteristics and Korean public health data.

## Target Users

- Biosensor startups
- University researchers
- Diagnostic companies

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, TypeScript, Tailwind, shadcn/ui |
| Backend | FastAPI (Python 3.12) |
| Database | Supabase (PostgreSQL + pgvector), Neo4j 5 |
| AI | OpenAI, RAG, Knowledge Graph, Recommendation Engine |
| Auth | Supabase Auth |
| Infra | Docker, Vercel (web), Railway (api/db) |

## Documentation

- [**System Architecture**](docs/SYSTEM_ARCHITECTURE.md) — diagrams, event flow, entities, API list, deployment
- [**Data Architecture**](docs/DATA_ARCHITECTURE.md) — Postgres + Neo4j schema, ORM, migrations, seeds
- [Architecture (deep-dive)](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Directory Structure](docs/DIRECTORY_STRUCTURE.md)
- [Supabase Setup](docs/SUPABASE.md)

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.12+ (local API development)

### 1. Environment

```bash
cp .env.example .env
# Edit .env with Supabase and OpenAI keys (see docs/SUPABASE.md)
```

### 2. Docker (full stack)

```bash
docker compose up -d
```

| Service | URL |
|---------|-----|
| Web | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |

### 3. Health Check

```bash
curl http://localhost:8000/v1/health
```

### 4. Local Development (without Docker)

**API:**

```bash
cd apps/api
pip install ".[dev]"
uvicorn biosense.api.main:app --reload --port 8000
```

**Web:**

```bash
cd apps/web
npm install
npm run dev
```

## Project Structure

```
apps/
  web/          # Next.js 15 frontend
  api/          # FastAPI backend (clean architecture)
packages/
  openapi/      # API contract (source of truth)
infra/
  db/migrations/  # PostgreSQL + Neo4j migrations
docs/           # Architecture & roadmap
```

## API Overview

| Endpoint | Description |
|----------|-------------|
| `GET /v1/health` | Health + dependency status |
| `GET /v1/me` | Current user (Supabase Auth) |
| `POST /v1/biomarker-cases` | Create biomarker input |
| `POST /v1/biomarker-cases/{id}/recommendations` | Run recommendation engine |
| `POST /v1/knowledge-graph/search` | Graph search |
| `GET /v1/public-data/cancer-stats` | Korean cancer statistics |

Full contract: [`packages/openapi/openapi.yaml`](packages/openapi/openapi.yaml)

## Implementation Status

| Phase | Status |
|-------|--------|
| 0 — Foundation | In progress |
| 1 — Auth & Dashboard | Planned |
| 2 — Biomarker Input | Planned |
| 3 — Public Data | Planned |
| 4 — Knowledge Graph | Planned |
| 5 — AI Recommendations | Planned |
| 6 — Production | Planned |

See [ROADMAP.md](docs/ROADMAP.md) for details.

## License

Proprietary — BioSense-GovAI
