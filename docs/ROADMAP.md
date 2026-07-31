# BioSense-GovAI — Implementation Roadmap

## Overview

Phased delivery from foundation → core MVP → production hardening. Each phase ends with **runnable, demoable** functionality.

| Phase | Duration | Goal |
|-------|----------|------|
| 0 — Foundation | Week 1 | Monorepo, Docker, CI, contracts |
| 1 — Auth & Shell | Week 2 | Login, dashboard shell, API health |
| 2 — Biomarker Input | Week 3 | Case CRUD, validation, persistence |
| 3 — Public Data | Week 4 | Korean health data integration |
| 4 — Knowledge Graph | Week 5–6 | Neo4j schema, search API, UI |
| 5 — AI & Recommendations | Week 7–8 | RAG + engine + full output |
| 6 — Production | Week 9–10 | Deploy, monitoring, polish |

---

## Phase 0 — Foundation (Current)

**Objective:** Establish monorepo, infrastructure, and API contracts.

### Deliverables

- [x] Architecture document
- [x] Roadmap document
- [x] Directory structure (`apps/`, `packages/`, `infra/`, `docs/`)
- [x] OpenAPI 3.1 specification
- [x] PostgreSQL migration `001_initial_schema.sql`
- [x] Neo4j seed script `001_constraints.cypher`
- [x] `docker-compose.yml` (postgres, neo4j, api, web)
- [x] `.env.example`
- [x] GitHub Actions CI workflow
- [x] Root README

### Exit Criteria

```bash
docker compose up -d
curl http://localhost:8000/v1/health   # {"status":"ok"}
curl http://localhost:3000               # Landing page loads
```

---

## Phase 1 — Authentication & Dashboard Shell

**Objective:** Clerk login and protected dashboard layout.

### Backend

- [ ] Clerk JWT verification middleware
- [ ] `GET /v1/me` — upsert user from Clerk claims
- [ ] `GET /v1/dashboard` — placeholder stats (case count = 0)

### Frontend

- [ ] Next.js 15 app with App Router
- [ ] Clerk provider + middleware (`/dashboard/*` protected)
- [ ] shadcn/ui setup (Button, Card, Sidebar, Table)
- [ ] Dashboard layout with navigation
- [ ] Sign-in / sign-up pages

### Exit Criteria

- User can sign in via Clerk
- Dashboard renders with sidebar nav (empty states)
- API rejects unauthenticated requests with 401

---

## Phase 2 — Biomarker Input

**Objective:** Full biomarker case lifecycle.

### Backend

- [ ] `POST /v1/biomarker-cases` with validation
  - `cancer_type` (enum)
  - `ctdna_class` (enum: fragmentomics, methylation, mutation, CNV)
  - `patient_age` (0–120)
  - `region_code` (KR administrative code)
- [ ] `GET /v1/biomarker-cases` (paginated, user-scoped)
- [ ] `GET /v1/biomarker-cases/{id}`
- [ ] Alembic migrations synced with SQL files

### Frontend

- [ ] `/biomarkers/new` — multi-step form
- [ ] `/biomarkers` — case list table
- [ ] `/biomarkers/[id]` — case detail view

### Exit Criteria

- Create, list, and view biomarker cases
- Data persisted in PostgreSQL
- Form validation with Zod + server-side Pydantic

---

## Phase 3 — Public Data Integration

**Objective:** Enrich cases with Korean public health statistics.

### Backend

- [ ] `KoreanHealthClient` adapter (KOSIS / KDCA open data)
- [ ] `GET /v1/public-data/regions` — 17 시도 + optional 시군구
- [ ] `GET /v1/public-data/cancer-stats?region=&cancer_type=&year=`
- [ ] Background job: cache stats in `public_health_stats`
- [ ] Link stats to biomarker case on creation

### Frontend

- [ ] `/public-data` — regional cancer incidence/mortality charts
- [ ] Region selector component (reused in biomarker form)
- [ ] Case detail: public data context panel

### Data Sources (MVP)

| Source | Data |
|--------|------|
| KOSIS | Cancer incidence by region |
| KDCA | Mortality statistics |
| Internal seed | Fallback static JSON for offline dev |

### Exit Criteria

- Selecting a region shows real or seeded public health data
- Case detail displays regional cancer context

---

## Phase 4 — Knowledge Graph

**Objective:** Searchable biomarker–biosensor relationship graph.

### Backend

- [ ] Neo4j connection pool + health check
- [ ] Seed data: 20+ ctDNA biomarkers, 10+ sensor types, 50+ literature nodes
- [ ] `POST /v1/knowledge-graph/search`
  - Full-text on node properties
  - Traversal: biomarker → recognition → sensor
- [ ] `GET /v1/knowledge-graph/nodes/{id}` — neighbors + properties

### Frontend

- [ ] `/knowledge-graph` — search UI + results list
- [ ] Graph visualization (react-force-graph or Cytoscape.js)
- [ ] Node detail drawer

### Exit Criteria

- Search "KRAS mutation ctDNA" returns compatible sensors
- Graph renders interactive neighborhood view

---

## Phase 5 — AI Recommendation Engine

**Objective:** End-to-end recommendation with all output fields.

### Backend

- [ ] Literature ingestion pipeline (seed 100+ abstracts)
- [ ] pgvector embedding + similarity search
- [ ] `RAGPipeline`: retrieve → rerank → context assembly
- [ ] `RecommendationEngine` use case:
  1. Load biomarker case
  2. Fetch public health context
  3. Query Neo4j for compatible strategies
  4. RAG for literature evidence
  5. GPT-4o structured output (JSON schema)
- [ ] `POST /v1/biomarker-cases/{id}/recommendations`
- [ ] `GET /v1/recommendations/{id}`

### Output Fields (all required)

| Field | Source |
|-------|--------|
| Sensor Type | KG + LLM |
| Recognition Strategy | KG compatibility edges |
| Expected Sensitivity | Literature + model estimate |
| Expected Specificity | Literature + model estimate |
| Expected LOD | KG metrics + literature |
| Estimated Cost | Rule-based + LLM |
| Experimental Protocol | RAG-grounded steps |

### Frontend

- [ ] "Generate Recommendations" button on case detail
- [ ] `/recommendations/[id]` — full results card
- [ ] Comparison table for top-3 strategies
- [ ] Export protocol as PDF (Phase 5 stretch)

### Exit Criteria

- Full pipeline produces 3 ranked recommendations in < 30s
- Each recommendation cites ≥ 1 literature source
- All 7 output fields populated

---

## Phase 6 — Production Hardening

**Objective:** Deploy to Vercel + Railway with monitoring.

### Infrastructure

- [ ] Railway: API + PostgreSQL + Neo4j services
- [ ] Vercel: Next.js with env vars
- [ ] Clerk production instance
- [ ] GitHub Actions deploy workflow
- [ ] Database backup strategy

### Quality

- [ ] API integration tests (pytest + testcontainers)
- [ ] E2E tests (Playwright): login → create case → recommend
- [ ] Rate limiting on `/recommendations`
- [ ] Sentry error tracking
- [ ] API documentation page (Scalar/Swagger UI)

### Exit Criteria

- Production URL accessible
- CI green on main branch
- E2E smoke test passes against staging

---

## Post-MVP Backlog

| Priority | Feature |
|----------|---------|
| P1 | Team/org workspaces (Clerk Organizations) |
| P1 | Recommendation history + diff |
| P2 | Bulk CSV import for biomarker cases |
| P2 | Custom literature upload (RAG) |
| P2 | Admin panel for KG curation |
| P3 | Fine-tuned domain model |
| P3 | Real-time sensor feasibility scoring API |
| P3 | Multi-language (EN/KO) |

---

## Risk Register

| Risk | Mitigation |
|------|------------|
| Korean public API rate limits | Local cache + seed fallback |
| OpenAI latency/cost | Cache embeddings; use gpt-4o-mini for drafts |
| Neo4j hosting cost on Railway | Start with Aura free tier or Docker sidecar |
| Hallucinated sensitivity values | Require literature citation; confidence score |
| Clerk + FastAPI JWT mismatch | Integration test in Phase 1 |

---

## Success Metrics (MVP)

| Metric | Target |
|--------|--------|
| Time to first recommendation | < 5 min (new user) |
| Recommendation latency (p95) | < 30 s |
| API uptime | 99.5% |
| User satisfaction (pilot) | ≥ 4/5 |
