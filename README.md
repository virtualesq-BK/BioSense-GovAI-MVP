# BioSense-GovAI

> 🇰🇷 [한국어](#한국어) · 🇺🇸 [English](#english)

AI-powered **biomarker–biosensor co-design** SaaS platform for early cancer detection, combining ctDNA molecular characteristics, Korean public health statistics, and literature-backed evidence.

---

<a id="한국어"></a>
## 한국어

### 1. 프로그램 개요

**BioSense-GovAI**는 암 조기진단용 **바이오마커-바이오센서 공동설계(co-design)**를 지원하는 AI SaaS 플랫폼입니다. 바이오센서 스타트업, 대학 연구자, 진단기기 기업을 대상으로, 특정 암종에 대해 어떤 ctDNA 바이오마커를 선택하고 어떤 인식 소자(recognition element)·트랜스듀서(transducer)로 센서를 설계해야 하는지에 대한 근거 기반 R&D 설계 리포트를 자동으로 생성합니다.

핵심 아이디어는 "감(perception)"이 아니라 **근거(evidence)** 기반 설계입니다:

- 국가암등록통계·KOSIS 등 **한국 공공 역학 데이터**로 암종/지역별 발생률·사망률을 제시
- **NCI GDC(Genomic Data Commons)** 연동으로 유전자 수준 변이·메틸화 데이터를 조회
- **PubMed 문헌 수집 + RAG(검색증강생성)**로 관련 논문 근거를 자동 인용
- 바이오마커 후보 스코어링 → DNA 하이브리다이제이션/CRISPR-Cas 인식 전략 → 전기화학/광학/압전/FET 센서 후보까지 이어지는 **파이프라인**으로 리포트를 구성
- 데이터가 없는 항목은 추정치로 꾸며내지 않고 "데이터 없음(Missing data)"으로 명시하여 **정직한 불확실성 표기**를 지향

### 2. 주요 기능 (화면 기준)

| 화면 | 설명 |
|------|------|
| `/dashboard` | 로그인 후 전체 현황 대시보드 |
| `/rnd-design` | **R&D 설계 리포트** — 암종/바이오마커 종류/타겟 유전자/지역/환자 연령을 입력하면, 역학적 근거 → 바이오마커 후보 → 분자적 특성 → 인식 전략 → 센서 후보 → 근거 문헌 → 실험 설계 가설 → 한계점 → 참고문헌까지 12단계 리포트와 바이오센서 파이프라인 다이어그램(검체→생체인식→트랜스듀서→신호판독)을 생성 |
| `/recommendations` | 바이오마커 케이스 기반 AI 추천 엔진 |
| `/reports` | 생성된 리포트 열람 |
| `/admin/literature` | 문헌(논문) 업로드/수집 상태 관리, RAG 품질 평가 |
| `/sign-in`, `/sign-up` | Supabase Auth 기반 인증 |

### 3. 기술 스택

| 계층 | 기술 |
|------|------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI (Python 3.12), Clean Architecture |
| Database | Supabase (PostgreSQL + pgvector), Neo4j 5 (지식 그래프) |
| AI | OpenAI (LLM/임베딩), RAG, Knowledge Graph, 추천 엔진 |
| 외部 데이터 소스 | KOSIS/KDCA(한국 공공데이터), NCI GDC(유전체), PubMed(문헌) |
| 인증 | Supabase Auth |
| 인프라 | Docker, Vercel(웹), Railway(API/DB — 선택) |

### 4. API 개요 (`/v1`)

| 그룹 | 대표 엔드포인트 |
|------|----------------|
| Health | `GET /v1/health` |
| Users | `GET /v1/me` |
| R&D 설계 | `POST /v1/rnd/design` — 암종·바이오마커로 12단계 설계 리포트 생성 |
| Biomarkers | `GET /v1/biomarkers/methylation-evidence` |
| Catalog | `GET /v1/cancers`, `/v1/biomarkers`, `/v1/sources`, `/v1/evidence`, `/v1/global-cancer-statistics` |
| Ingestion | `POST /v1/ingestion/jobs/trigger`, `GET /v1/ingestion/jobs`, `GET /v1/public-data/cancer-stats` |
| Literature/RAG | `GET/POST /v1/literature/papers*`, `POST /v1/literature/rag/query`, `POST /v1/literature/rag/evaluate` |
| Recommendations | `POST /v1/recommendations/generate` |
| Knowledge Graph | `POST /v1/sync/schema`, `/v1/sync/domain`, `/v1/sync/gene` |

전체 계약: [`packages/openapi/openapi.yaml`](packages/openapi/openapi.yaml) · 대화형 문서: `http://localhost:8000/docs`

### 5. 실행 방법

#### 사전 요구사항

- Docker & Docker Compose
- Node.js 20+
- Python 3.12+ (API를 Docker 없이 로컬 실행할 경우)

#### 5-1. 환경 변수 설정

```bash
cp .env.example .env
# .env를 열어 Supabase, OpenAI 등의 키를 입력 (docs/SUPABASE.md 참고)
```

주요 항목:
- `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL`
- (선택) `KOSIS_API_KEY`, `KDCA_API_URL/KEY`, `PUBMED_API_KEY` — 미설정 시 시드 JSON으로 폴백

#### 5-2. Docker Compose로 전체 스택 실행 (권장)

```bash
docker compose up -d
```

| 서비스 | 주소 |
|--------|------|
| Web | http://localhost:3000 |
| API | http://localhost:8000 |
| API 문서(Swagger) | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |

헬스체크:

```bash
curl http://localhost:8000/v1/health
```

#### 5-3. Docker 없이 로컬 개발

**API 서버:**

```bash
cd apps/api
pip install ".[dev]"
uvicorn biosense.api.main:app --reload --port 8000
```

**웹 프론트엔드:**

```bash
cd apps/web
npm install
npm run dev
```

기본적으로 웹은 `/api/*` 요청을 `API_URL`(기본 `http://127.0.0.1:8000`)로 프록시합니다 ([next.config.ts](apps/web/next.config.ts)).

#### 5-4. 테스트

```bash
# API 단위 테스트
cd apps/api
pytest

# 웹 타입 체크
cd apps/web
npx tsc --noEmit
```

### 6. 프로젝트 구조

```
apps/
  web/          # Next.js 15 프론트엔드 (App Router)
  api/          # FastAPI 백엔드 (도메인/애플리케이션/인프라 계층 분리)
packages/
  openapi/      # API 계약 정의 (source of truth)
infra/
  db/migrations/  # PostgreSQL + Neo4j 마이그레이션
docs/           # 아키텍처 및 로드맵 문서
```

### 7. 배포

- **웹(Next.js)**: Vercel 프로젝트에 연결됨 (`apps/web`, standalone 빌드) — `vercel --prod` 또는 Vercel Git 연동으로 자동 배포
- **API/DB**: Railway 또는 임의의 Docker 호스트에 `apps/api/Dockerfile`로 배포. 배포 환경에서는 `.env`의 `NEXT_PUBLIC_API_URL`을 실제 API 도메인으로 지정해야 함

### 8. 문서

- [시스템 아키텍처](docs/SYSTEM_ARCHITECTURE.md) — 다이어그램, 이벤트 흐름, 엔티티, API 목록, 배포
- [데이터 아키텍처](docs/DATA_ARCHITECTURE.md) — Postgres + Neo4j 스키마, ORM, 마이그레이션, 시드
- [아키텍처 심화](docs/ARCHITECTURE.md)
- [로드맵](docs/ROADMAP.md)
- [디렉터리 구조](docs/DIRECTORY_STRUCTURE.md)
- [Supabase 설정](docs/SUPABASE.md)

### 9. 라이선스

Proprietary — BioSense-GovAI

---

<a id="english"></a>
## English

### 1. Overview

**BioSense-GovAI** is an AI-powered SaaS platform for **biomarker–biosensor co-design** in early cancer detection. It targets biosensor startups, university researchers, and diagnostic-device companies, automatically generating an evidence-backed R&D design report that answers: *which ctDNA biomarker should we target, and which recognition element / transducer should the sensor use, for a given cancer type?*

The platform is built around **evidence over intuition**:

- Real **Korean public epidemiological data** (national cancer registry / KOSIS) for incidence and mortality by cancer type and region
- **NCI GDC (Genomic Data Commons)** integration for gene-level mutation and methylation data
- **PubMed literature ingestion + RAG (Retrieval-Augmented Generation)** to automatically cite supporting papers
- A pipeline that scores biomarker candidates, proposes a DNA-hybridization / CRISPR-Cas recognition strategy, and ranks electrochemical / optical / piezoelectric / FET-based sensor candidates
- Any field without real data is explicitly labeled **"No data"** rather than fabricated — the platform never invents numbers to fill gaps

### 2. Key Features (by screen)

| Screen | Description |
|--------|-------------|
| `/dashboard` | Post-login overview dashboard |
| `/rnd-design` | **R&D Design Report** — enter cancer type, biomarker class, target gene, region, and patient age to generate a 12-section report (epidemiological evidence → biomarker candidates → molecular characteristics → recognition strategy → sensor candidates → supporting literature → experimental design hypothesis → limitations → references), plus a biosensor pipeline diagram (sample → biorecognition → transducer → signal readout) |
| `/recommendations` | AI recommendation engine driven by a biomarker case |
| `/reports` | Browse previously generated reports |
| `/admin/literature` | Manage paper uploads/ingestion status and RAG quality evaluation |
| `/sign-in`, `/sign-up` | Supabase Auth-based authentication |

### 3. Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI (Python 3.12), Clean Architecture |
| Database | Supabase (PostgreSQL + pgvector), Neo4j 5 (knowledge graph) |
| AI | OpenAI (LLM/embeddings), RAG, Knowledge Graph, recommendation engine |
| External data | KOSIS/KDCA (Korean public data), NCI GDC (genomics), PubMed (literature) |
| Auth | Supabase Auth |
| Infra | Docker, Vercel (web), Railway (api/db — optional) |

### 4. API Overview (`/v1`)

| Group | Representative endpoints |
|-------|---------------------------|
| Health | `GET /v1/health` |
| Users | `GET /v1/me` |
| R&D Design | `POST /v1/rnd/design` — generates the 12-section design report for a cancer/biomarker pair |
| Biomarkers | `GET /v1/biomarkers/methylation-evidence` |
| Catalog | `GET /v1/cancers`, `/v1/biomarkers`, `/v1/sources`, `/v1/evidence`, `/v1/global-cancer-statistics` |
| Ingestion | `POST /v1/ingestion/jobs/trigger`, `GET /v1/ingestion/jobs`, `GET /v1/public-data/cancer-stats` |
| Literature/RAG | `GET/POST /v1/literature/papers*`, `POST /v1/literature/rag/query`, `POST /v1/literature/rag/evaluate` |
| Recommendations | `POST /v1/recommendations/generate` |
| Knowledge Graph | `POST /v1/sync/schema`, `/v1/sync/domain`, `/v1/sync/gene` |

Full contract: [`packages/openapi/openapi.yaml`](packages/openapi/openapi.yaml) · Interactive docs: `http://localhost:8000/docs`

### 5. Getting Started

#### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.12+ (only needed to run the API without Docker)

#### 5-1. Environment

```bash
cp .env.example .env
# Fill in Supabase, OpenAI, and other keys (see docs/SUPABASE.md)
```

Key variables:
- `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL`
- (optional) `KOSIS_API_KEY`, `KDCA_API_URL/KEY`, `PUBMED_API_KEY` — fall back to seed JSON if unset

#### 5-2. Full stack via Docker Compose (recommended)

```bash
docker compose up -d
```

| Service | URL |
|---------|-----|
| Web | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |

Health check:

```bash
curl http://localhost:8000/v1/health
```

#### 5-3. Local development without Docker

**API server:**

```bash
cd apps/api
pip install ".[dev]"
uvicorn biosense.api.main:app --reload --port 8000
```

**Web frontend:**

```bash
cd apps/web
npm install
npm run dev
```

By default the web app proxies `/api/*` requests to `API_URL` (default `http://127.0.0.1:8000`) — see [next.config.ts](apps/web/next.config.ts).

#### 5-4. Tests

```bash
# API unit tests
cd apps/api
pytest

# Web type check
cd apps/web
npx tsc --noEmit
```

### 6. Project Structure

```
apps/
  web/          # Next.js 15 frontend (App Router)
  api/          # FastAPI backend (domain/application/infrastructure layers)
packages/
  openapi/      # API contract (source of truth)
infra/
  db/migrations/  # PostgreSQL + Neo4j migrations
docs/           # Architecture & roadmap docs
```

### 7. Deployment

- **Web (Next.js)**: linked to a Vercel project (`apps/web`, standalone build) — deploy with `vercel --prod` or via Vercel's Git integration
- **API/DB**: deploy `apps/api/Dockerfile` to Railway or any Docker host. In production, set `NEXT_PUBLIC_API_URL` in the web app's environment to the real API domain

### 8. Documentation

- [System Architecture](docs/SYSTEM_ARCHITECTURE.md) — diagrams, event flow, entities, API list, deployment
- [Data Architecture](docs/DATA_ARCHITECTURE.md) — Postgres + Neo4j schema, ORM, migrations, seeds
- [Architecture (deep-dive)](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Directory Structure](docs/DIRECTORY_STRUCTURE.md)
- [Supabase Setup](docs/SUPABASE.md)

### 9. License

Proprietary — BioSense-GovAI
