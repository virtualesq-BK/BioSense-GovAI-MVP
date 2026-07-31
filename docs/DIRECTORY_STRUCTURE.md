# BioSense-GovAI — Directory Structure

Monorepo layout. Canonical contract: `packages/openapi/openapi.yaml`.

```
BioSense-GovAI/
│
├── apps/
│   ├── web/                              # Next.js 15 frontend (Vercel)
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── (auth)/
│   │   │   │   │   ├── sign-in/[[...sign-in]]/page.tsx
│   │   │   │   │   └── sign-up/[[...sign-up]]/page.tsx
│   │   │   │   ├── (dashboard)/
│   │   │   │   │   ├── layout.tsx
│   │   │   │   │   ├── dashboard/page.tsx
│   │   │   │   │   ├── biomarkers/
│   │   │   │   │   │   ├── page.tsx
│   │   │   │   │   │   ├── new/page.tsx
│   │   │   │   │   │   └── [id]/page.tsx
│   │   │   │   │   ├── knowledge-graph/page.tsx
│   │   │   │   │   ├── public-data/page.tsx
│   │   │   │   │   └── recommendations/[id]/page.tsx
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx
│   │   │   │   └── globals.css
│   │   │   ├── components/
│   │   │   │   ├── ui/                   # shadcn/ui
│   │   │   │   └── features/
│   │   │   │       ├── dashboard/
│   │   │   │       ├── biomarkers/
│   │   │   │       ├── knowledge-graph/
│   │   │   │       └── recommendations/
│   │   │   ├── lib/
│   │   │   │   ├── api-client.ts
│   │   │   │   └── utils.ts
│   │   │   ├── hooks/
│   │   │   └── types/
│   │   │       └── api.ts                # Generated from OpenAPI
│   │   ├── public/
│   │   ├── Dockerfile
│   │   ├── next.config.ts
│   │   ├── package.json
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   └── components.json               # shadcn config
│   │
│   └── api/                              # FastAPI backend (Railway)
│       ├── src/
│       │   └── biosense/
│       │       ├── __init__.py
│       │       ├── api/
│       │       │   ├── main.py
│       │       │   ├── dependencies.py
│       │       │   └── v1/
│       │       │       ├── router.py
│       │       │       ├── health.py
│       │       │       ├── users.py
│       │       │       ├── dashboard.py
│       │       │       ├── biomarker_cases.py
│       │       │       ├── recommendations.py
│       │       │       ├── knowledge_graph.py
│       │       │       └── public_data.py
│       │       ├── application/
│       │       │   ├── dto/
│       │       │   └── use_cases/
│       │       ├── domain/
│       │       │   ├── entities/
│       │       │   ├── value_objects/
│       │       │   ├── repositories/
│       │       │   └── services/
│       │       └── infrastructure/
│       │           ├── persistence/
│       │           │   ├── postgres/
│       │           │   └── neo4j/
│       │           ├── ai/
│       │           ├── external/
│       │           └── auth/
│       ├── tests/
│       │   ├── unit/
│       │   └── integration/
│       ├── alembic/
│       │   ├── versions/
│       │   └── env.py
│       ├── Dockerfile
│       ├── pyproject.toml
│       └── alembic.ini
│
├── packages/
│   └── openapi/
│       ├── openapi.yaml                  # API contract (source of truth)
│       └── README.md
│
├── infra/
│   ├── db/
│   │   └── migrations/
│   │       ├── postgres/
│   │       │   └── 001_initial_schema.sql
│   │       └── neo4j/
│   │           ├── 001_constraints.cypher
│   │           └── 002_seed_data.cypher
│   └── seed/
│       └── public_health/
│           └── kr_cancer_stats.json      # Offline dev fallback
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   └── DIRECTORY_STRUCTURE.md            # This file
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
│
├── docker-compose.yml
├── .env.example
├── package.json                          # npm workspaces root
├── README.md
└── .gitignore
```

## Package Boundaries

| Path | Runtime | Deploy Target |
|------|---------|---------------|
| `apps/web` | Node.js 20 | Vercel |
| `apps/api` | Python 3.12 | Railway |
| `packages/openapi` | — | Contract only |
| `infra/` | — | Migrations & seeds |

## Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| API routes | kebab-case, versioned | `/v1/biomarker-cases` |
| Python modules | snake_case | `biomarker_cases.py` |
| React components | PascalCase | `BiomarkerForm.tsx` |
| DB tables | snake_case plural | `biomarker_cases` |
| Env vars | SCREAMING_SNAKE | `DATABASE_URL` |

## Legacy Note

The repository root may still contain the original SvelteKit scaffold (`src/`, `vite.config.ts`). It will be removed in Phase 1 when `apps/web` (Next.js) is initialized. All new development uses the `apps/` structure above.
