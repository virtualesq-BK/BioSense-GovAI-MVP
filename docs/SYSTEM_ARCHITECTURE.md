# BioSense-GovAI — System Architecture

> Optimized for **low cost**, **solo founder**, and **Cursor IDE** compatibility.

| Layer | Technology | Cost Strategy |
|-------|------------|---------------|
| Frontend | Next.js 15 + TypeScript + Tailwind + shadcn/ui | Vercel Hobby (free) |
| Backend | FastAPI (Python 3.12) | Railway Hobby (~$5/mo) |
| AI | OpenAI (GPT-4o + embeddings) | Cache embeddings in Postgres |
| Graph | Neo4j 5 Community | Aura Free tier or Docker sidecar |
| Search | RAG (pgvector) | Same Postgres instance — no Pinecone |
| Storage | PostgreSQL 16 + pgvector | Railway managed Postgres |
| Auth | Clerk | Free tier (10k MAU) |

**Deliberately excluded (MVP):** Redis, Kafka, Kubernetes, separate vector DB, microservices split.

---

## 1. Architecture Diagram

### 1.1 Logical Architecture

```mermaid
flowchart TB
  subgraph users [Users]
    U1[Startup]
    U2[Researcher]
    U3[Diagnostic Co.]
  end

  subgraph vercel [Vercel — Free Tier]
    NEXT[Next.js 15 App Router]
    RSC[Server Components]
    CC[Client Components]
    NEXT --> RSC
    NEXT --> CC
  end

  subgraph clerk [Clerk — Free Tier]
    AUTH[Auth + JWT]
  end

  subgraph railway [Railway — Hobby Tier]
    API[FastAPI Monolith]
    subgraph layers [Clean Architecture]
      ROUTES[api/v1 routes]
      UC[use_cases]
      DOM[domain]
      INFRA[infrastructure]
      ROUTES --> UC --> DOM
      UC --> INFRA
    end
    API --> layers
  end

  subgraph storage [Storage — Single Region]
  PG[(PostgreSQL + pgvector)]
  NEO[(Neo4j)]
  end

  subgraph ai [AI Layer — Pay-per-use]
    OAI[OpenAI API]
    RAG[RAG Pipeline]
    REC[Recommendation Engine]
    RAG --> OAI
    REC --> RAG
    REC --> NEO
  end

  subgraph external [External — Optional]
    KOSIS[Korean Public Data]
    PUB[PubMed / Literature]
  end

  U1 & U2 & U3 --> NEXT
  NEXT <--> AUTH
  NEXT -->|REST + JWT| API
  API <--> AUTH
  INFRA --> PG
  INFRA --> NEO
  INFRA --> ai
  INFRA --> KOSIS
  RAG --> PG
  RAG --> PUB
```

### 1.2 Data Plane vs Control Plane

```mermaid
flowchart LR
  subgraph control [Control Plane — Solo Founder Ops]
    GH[GitHub]
    CI[GitHub Actions CI]
    CURSOR[Cursor IDE]
    OPENAPI[packages/openapi]
    GH --> CI
    CURSOR --> OPENAPI
    OPENAPI -->|codegen| NEXT2[apps/web/types]
    OPENAPI -->|contract| API2[apps/api]
  end

  subgraph data [Data Plane — Runtime]
    NEXT2 --> API2
    API2 --> PG2[(Postgres)]
    API2 --> NEO2[(Neo4j)]
    API2 --> OAI2[OpenAI]
  end
```

### 1.3 Solo-Founder Simplification Rules

| Instead of | Use | Saves |
|------------|-----|-------|
| Celery + Redis | FastAPI `BackgroundTasks` | ~$7/mo + ops time |
| Pinecone / Weaviate | pgvector in Postgres | ~$70/mo |
| Microservices | Single FastAPI monolith | Cognitive load |
| Kafka | DB status column + polling | Infra complexity |
| k8s | Railway + Vercel | $100+/mo |
| Custom auth | Clerk | Weeks of dev |

---

## 2. Folder Structure

Monorepo — **one Cursor workspace**, clear boundaries, OpenAPI as contract hub.

```
BioSense-GovAI/
│
├── .cursor/
│   └── rules/
│       └── biosense.mdc              # Cursor agent conventions
│
├── apps/
│   ├── web/                          # Next.js — TypeScript only
│   │   └── src/
│   │       ├── app/                  # Routes (RSC-first)
│   │       ├── components/
│   │       │   ├── ui/               # shadcn primitives
│   │       │   └── features/         # Domain UI (1 folder per feature)
│   │       ├── lib/
│   │       │   └── api-client.ts     # Typed fetch → FastAPI
│   │       └── types/
│   │           └── api.ts            # Generated from OpenAPI
│   │
│   └── api/                          # FastAPI — Python only
│       └── src/biosense/
│           ├── api/v1/               # HTTP handlers (thin)
│           ├── application/
│           │   ├── use_cases/        # 1 file per user action
│           │   └── dto/              # Pydantic request/response
│           ├── domain/
│           │   ├── entities/
│           │   ├── value_objects/
│           │   ├── repositories/     # Abstract ports
│           │   └── services/         # RecommendationEngine, RAG
│           └── infrastructure/
│               ├── persistence/
│               │   ├── postgres/     # SQLAlchemy repos
│               │   └── neo4j/        # Cypher queries
│               ├── ai/
│               │   ├── openai_client.py
│               │   ├── rag_pipeline.py
│               │   └── embedding_service.py
│               ├── external/         # KOSIS, PubMed
│               └── auth/               # Clerk JWT
│
├── packages/
│   └── openapi/
│       └── openapi.yaml              # ★ Single source of truth
│
├── infra/
│   ├── db/migrations/
│   │   ├── postgres/                 # SQL migrations
│   │   └── neo4j/                    # Cypher seeds
│   └── seed/                         # Offline dev JSON
│
├── docs/
│   ├── SYSTEM_ARCHITECTURE.md        # This file
│   ├── ARCHITECTURE.md               # Deep-dive ADRs
│   └── ROADMAP.md
│
├── docker-compose.yml                # Local full stack
├── .env.example
└── package.json                      # npm workspaces (web only)
```

### Cursor Compatibility Conventions

| Rule | Why |
|------|-----|
| **One feature = one use_case file** | Cursor can edit a single 80-line file safely |
| **OpenAPI before implementation** | Agent generates matching frontend + backend |
| **`apps/web` ↔ `apps/api` never import each other** | Clear tool boundaries |
| **Max 3 levels in `components/features/`** | Predictable navigation for AI |
| **SQL migrations are numbered** | Agent can append `002_*.sql` without conflict |
| **No shared runtime package (yet)** | Avoids TS↔Python bridge complexity |

---

## 3. Event Flow

### 3.1 Primary Flow — Generate Recommendation

```mermaid
sequenceDiagram
  actor User
  participant Web as Next.js
  participant Clerk
  participant API as FastAPI
  participant PG as PostgreSQL
  participant Neo as Neo4j
  participant RAG as RAG Pipeline
  participant OAI as OpenAI

  User->>Web: Submit biomarker case
  Web->>Clerk: Get session JWT
  Web->>API: POST /v1/biomarker-cases
  API->>Clerk: Verify JWT (JWKS)
  API->>PG: INSERT biomarker_case
  API->>PG: SELECT public_health_stats (region)
  API-->>Web: 201 Case created

  User->>Web: Click "Generate Recommendations"
  Web->>API: POST /v1/biomarker-cases/{id}/recommendations
  API->>PG: UPDATE status → processing

  par Graph lookup
    API->>Neo: MATCH biomarker→recognition→sensor
    Neo-->>API: Compatible strategies
  and RAG retrieval
    API->>RAG: Build query from case context
    RAG->>OAI: Embed query
    RAG->>PG: vector similarity search
    PG-->>RAG: Top-k literature chunks
    RAG->>OAI: Rerank (optional, gpt-4o-mini)
    RAG-->>API: Grounded passages
  end

  API->>OAI: Structured completion (JSON schema)
  OAI-->>API: 3 ranked recommendations
  API->>PG: INSERT recommendations
  API->>PG: UPDATE status → recommended
  API-->>Web: 202 RecommendationList
  Web-->>User: Sensor type, LOD, protocol, etc.
```

### 3.2 Knowledge Graph Search Flow

```mermaid
sequenceDiagram
  participant Web as Next.js
  participant API as FastAPI
  participant Neo as Neo4j
  participant PG as PostgreSQL

  Web->>API: POST /v1/knowledge-graph/search
  API->>Neo: Full-text + label filter
  Neo-->>API: Matching nodes
  API->>Neo: Expand neighbors (depth=1)
  Neo-->>API: Subgraph
  opt Semantic boost
    API->>PG: pgvector similarity on literature
    PG-->>API: Related papers
  end
  API-->>Web: Nodes + relationships
```

### 3.3 Background Events (No Message Broker)

```mermaid
stateDiagram-v2
  [*] --> draft: POST biomarker-case
  draft --> submitted: User confirms
  submitted --> processing: POST recommendations
  processing --> recommended: Engine success
  processing --> failed: Engine error
  failed --> submitted: Retry
  recommended --> [*]
```

| Event | Trigger | Handler | Storage |
|-------|---------|---------|---------|
| `case.created` | POST biomarker-cases | Sync | Postgres INSERT |
| `case.enriched` | After create | Sync fetch public data | Postgres cache |
| `recommendation.requested` | POST …/recommendations | FastAPI BackgroundTask | Status column |
| `recommendation.completed` | Engine done | Sync | Postgres INSERT |
| `literature.ingested` | Admin/cron (weekly) | Script | Postgres + pgvector |

> **Solo-founder note:** Status polling from frontend (`GET /v1/biomarker-cases/{id}`) replaces WebSockets/SSE until scale demands it.

---

## 4. Entity Diagram

### 4.1 PostgreSQL (Relational + Vectors)

```mermaid
erDiagram
  users ||--o{ biomarker_cases : owns
  biomarker_cases ||--o{ recommendations : generates
  literature_documents ||--o{ literature_chunks : contains

  users {
    uuid id PK
    text clerk_id UK
    text email
    text role
    timestamptz created_at
  }

  biomarker_cases {
    uuid id PK
    uuid user_id FK
    text cancer_type
    text ctdna_class
    int patient_age
    text region_code
    text status
    timestamptz created_at
  }

  recommendations {
    uuid id PK
    uuid biomarker_case_id FK
    int rank
    text sensor_type
    text recognition_strategy
    numeric expected_sensitivity
    numeric expected_specificity
    numeric expected_lod_value
    text expected_lod_unit
    numeric estimated_cost_usd
    jsonb experimental_protocol
    numeric confidence_score
    jsonb evidence
  }

  public_health_stats {
    uuid id PK
    text region_code
    text cancer_type
    numeric incidence_rate
    numeric mortality_rate
    int data_year
    text source
  }

  literature_documents {
    uuid id PK
    text external_id UK
    text title
    text[] authors
    date published_at
    text source
  }

  literature_chunks {
    uuid id PK
    uuid document_id FK
    int chunk_index
    text content
    vector embedding
  }
```

### 4.2 Neo4j (Knowledge Graph)

```mermaid
graph TB
  subgraph biomarkers [Biomarker Domain]
    CTDNA[CtDnaBiomarker]
    CANCER[CancerType]
    CTDNA -->|EXPRESSED_IN| CANCER
  end

  subgraph sensors [Sensor Domain]
    RECOG[RecognitionElement]
    SENSOR[SensorPlatform]
    METRIC[PerformanceMetric]
    RECOG -->|USED_IN| SENSOR
    SENSOR -->|HAS_LOD| METRIC
  end

  subgraph evidence [Evidence Domain]
    PAPER[Literature]
    REGION[KrRegion]
  end

  CTDNA -->|COMPATIBLE_WITH| RECOG
  CTDNA -->|CITED_IN| PAPER
  SENSOR -->|CITED_IN| PAPER
  REGION -->|HAS_INCIDENCE| CANCER
  REGION -->|HAS_MORTALITY| CANCER
  SENSOR -->|RECOMMENDED_FOR| CTDNA
```

### 4.3 Cross-Store Mapping

| Concept | Postgres | Neo4j |
|---------|----------|-------|
| User case | `biomarker_cases` row | — |
| Biomarker definition | Referenced by `ctdna_class` enum | `CtDnaBiomarker` node |
| Sensor strategy | `recommendations` row | Traversed path |
| Literature evidence | `literature_chunks` + embedding | `Literature` node + `CITED_IN` |
| Regional stats | `public_health_stats` cache | `KrRegion`→`CancerType` edges |

---

## 5. API List

Canonical spec: [`packages/openapi/openapi.yaml`](../packages/openapi/openapi.yaml)

### 5.1 Endpoints

| # | Method | Path | Tag | Auth | Description |
|---|--------|------|-----|------|-------------|
| 1 | `GET` | `/v1/health` | Health | — | Liveness + Postgres/Neo4j status |
| 2 | `GET` | `/v1/me` | Users | JWT | Current user profile (Clerk sync) |
| 3 | `GET` | `/v1/dashboard` | Dashboard | JWT | Case count, recent activity |
| 4 | `GET` | `/v1/biomarker-cases` | Biomarker Cases | JWT | Paginated list (`page`, `page_size`) |
| 5 | `POST` | `/v1/biomarker-cases` | Biomarker Cases | JWT | Create case (cancer, ctDNA, age, region) |
| 6 | `GET` | `/v1/biomarker-cases/{caseId}` | Biomarker Cases | JWT | Case detail + public data context |
| 7 | `POST` | `/v1/biomarker-cases/{caseId}/recommendations` | Recommendations | JWT | Run AI recommendation engine |
| 8 | `GET` | `/v1/recommendations/{recommendationId}` | Recommendations | JWT | Full recommendation output |
| 9 | `GET` | `/v1/public-data/regions` | Public Data | JWT | Korean administrative regions |
| 10 | `GET` | `/v1/public-data/cancer-stats` | Public Data | JWT | Incidence/mortality by region |
| 11 | `POST` | `/v1/knowledge-graph/search` | Knowledge Graph | JWT | Full-text + type-filtered search |
| 12 | `GET` | `/v1/knowledge-graph/nodes/{nodeId}` | Knowledge Graph | JWT | Node + neighbors (`depth=1..3`) |

### 5.2 Recommendation Output Contract

Every `POST …/recommendations` returns ranked items with:

| Field | Type | Example |
|-------|------|---------|
| `sensor_type` | enum | `electrochemical` |
| `recognition_strategy` | enum | `aptamer_based` |
| `expected_sensitivity` | 0–1 | `0.92` |
| `expected_specificity` | 0–1 | `0.95` |
| `expected_lod` | `{value, unit}` | `{0.1, "ng/mL"}` |
| `estimated_cost_usd` | number | `45.00` |
| `experimental_protocol` | `{steps, reagents, duration_hours}` | — |
| `confidence_score` | 0–1 | `0.87` |
| `evidence` | `{literature_ids, graph_paths}` | — |

### 5.3 Auth Model

```
Authorization: Bearer <clerk_session_jwt>
```

FastAPI validates via Clerk JWKS. User row upserted on first `GET /v1/me`.

---

## 6. Deployment Topology

### 6.1 Production

```mermaid
flowchart TB
  subgraph internet [Internet]
    USER[Browser]
  end

  subgraph vercel [Vercel — $0/mo]
    CDN[Edge CDN]
    NEXT[Next.js SSR/Static]
    CDN --> NEXT
  end

  subgraph clerk_cloud [Clerk — $0/mo]
    CLERK[Auth Service]
  end

  subgraph railway [Railway — ~$5–20/mo]
    direction TB
    API_SVC[FastAPI Service]
    PG_SVC[(PostgreSQL + pgvector)]
    API_SVC --> PG_SVC
  end

  subgraph neo4j_cloud [Neo4j Aura — $0 free tier]
    NEO_SVC[(Neo4j Graph)]
  end

  subgraph openai_cloud [OpenAI — Pay per use]
    OAI[API]
  end

  USER --> CDN
  USER --> CLERK
  NEXT -->|HTTPS + JWT| API_SVC
  NEXT --> CLERK
  API_SVC --> CLERK
  API_SVC --> NEO_SVC
  API_SVC --> OAI
```

### 6.2 Local Development (Docker Compose)

```mermaid
flowchart LR
  DEV[Developer + Cursor]

  subgraph docker [docker-compose.yml]
    WEB[web :3000]
    API[api :8000]
    PG[(postgres :5432)]
    NEO[(neo4j :7474/7687)]
  end

  DEV --> WEB
  DEV --> API
  WEB --> API
  API --> PG
  API --> NEO
```

```bash
cp .env.example .env
docker compose up -d
```

### 6.3 CI/CD Pipeline

```mermaid
flowchart LR
  PUSH[git push] --> CI[GitHub Actions]

  CI --> LINT[Lint TS + Python]
  CI --> TEST[pytest + tsc]
  CI --> OAPI[Validate OpenAPI]
  CI --> DOCKER[Docker build smoke]

  DOCKER -->|main branch| DEPLOY

  subgraph DEPLOY [Auto Deploy]
    V[Vercel — apps/web]
    R[Railway — apps/api]
  end
```

Workflows: `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`

### 6.4 Environment Matrix

| Variable | Local | Vercel | Railway |
|----------|-------|--------|---------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | `https://api.*.railway.app` | — |
| `DATABASE_URL` | Docker Postgres | — | Auto-injected |
| `NEO4J_URI` | `bolt://localhost:7687` | — | Aura connection string |
| `OPENAI_API_KEY` | `.env` | — | Railway secret |
| `CLERK_SECRET_KEY` | `.env` | Vercel env | Railway secret |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | `.env` | Vercel env | — |

### 6.5 Estimated Monthly Cost (Solo MVP)

| Service | Tier | Cost |
|---------|------|------|
| Vercel | Hobby | $0 |
| Railway | Hobby (API + Postgres) | ~$5–10 |
| Neo4j Aura | Free | $0 |
| Clerk | Free | $0 |
| GitHub Actions | Free (2000 min) | $0 |
| OpenAI | Usage-based | ~$10–30 |
| **Total** | | **~$15–40/mo** |

---

## Quick Reference

| Need | Go to |
|------|-------|
| API contract | `packages/openapi/openapi.yaml` |
| SQL schema | `infra/db/migrations/postgres/` |
| Graph seeds | `infra/db/migrations/neo4j/` |
| Run locally | `docker compose up -d` |
| Implementation plan | `docs/ROADMAP.md` |
| Cursor agent rules | `.cursor/rules/biosense.mdc` |
