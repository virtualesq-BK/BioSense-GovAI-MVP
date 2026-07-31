# BioSense-GovAI — Data Architecture

> Dual-store design: **PostgreSQL** (relational catalog + RAG + transactions) and **Neo4j** (graph traversal for co-design paths).

## Entity Overview

| Entity | Postgres Table | Neo4j Label | Purpose |
|--------|----------------|-------------|---------|
| Cancer | `cancers` | `Cancer` | Cancer type taxonomy |
| Biomarker | `biomarkers` | `Biomarker` | ctDNA-detectable marker |
| CtDNA | `ctdna` | `CtDNA` | Molecular class (mutation, methylation, …) |
| RecognitionStrategy | `recognition_strategies` | `RecognitionStrategy` | Molecular recognition approach |
| Sensor | `sensors` | `Sensor` | Biosensor platform |
| Performance | `sensor_performances` | `Performance` | Sensitivity, specificity, LOD |
| Paper | `papers` | `Paper` | Scientific literature (RAG source) |
| Protocol | `protocols` | `Protocol` | Experimental procedure |
| PublicHealthFeature | `public_health_features` | `PublicHealthFeature` | Korean regional cancer stats |

---

## Relationship Model

### Core Chain (User-specified)

```mermaid
graph LR
  Cancer -->|HAS| Biomarker
  Biomarker -->|MATCHES| RecognitionStrategy
  RecognitionStrategy -->|USES| Sensor
  Sensor -->|GENERATES| Performance
```

### Extended Relationships

```mermaid
graph TB
  Biomarker -->|OF_CLASS| CtDNA
  Biomarker -->|CITED_IN| Paper
  Sensor -->|CITED_IN| Paper
  Protocol -->|DESCRIBES| Sensor
  Protocol -->|SUPPORTED_BY| Paper
  PublicHealthFeature -->|FOR_CANCER| Cancer
```

### Postgres Junction Tables

| Relationship | Table | Key Columns |
|--------------|-------|-------------|
| Cancer HAS Biomarker | `cancer_biomarkers` | `cancer_id`, `biomarker_id` |
| Biomarker MATCHES Recognition | `biomarker_recognition_matches` | `match_score`, `mechanism` |
| Recognition USES Sensor | `recognition_sensor_uses` | `efficiency` |
| Sensor GENERATES Performance | `sensor_performances` | `sensitivity`, `specificity`, `lod_*` |
| Paper ↔ Biomarker | `paper_biomarkers` | M:N |
| Paper ↔ Sensor | `paper_sensors` | M:N |

---

## PostgreSQL ER Diagram

```mermaid
erDiagram
  ctdna ||--o{ biomarkers : classifies
  cancers ||--o{ cancer_biomarkers : has
  biomarkers ||--o{ cancer_biomarkers : linked
  biomarkers ||--o{ biomarker_recognition_matches : matches
  recognition_strategies ||--o{ biomarker_recognition_matches : matched_by
  recognition_strategies ||--o{ recognition_sensor_uses : uses
  sensors ||--o{ recognition_sensor_uses : used_in
  sensors ||--o{ sensor_performances : generates
  papers ||--o{ paper_chunks : chunked_for_rag
  papers ||--o{ paper_biomarkers : cites
  biomarkers ||--o{ paper_biomarkers : cited_in
  sensors ||--o{ protocols : described_by
  papers ||--o{ protocols : supports
  cancers ||--o{ public_health_features : regional_stats

  ctdna {
    uuid id PK
    text code UK
    text name
  }

  cancers {
    uuid id PK
    text code UK
    text name_en
    text name_ko
  }

  biomarkers {
    uuid id PK
    text name UK
    uuid ctdna_id FK
    text gene_symbol
    text neo4j_id UK
  }

  recognition_strategies {
    uuid id PK
    text code UK
    text name
  }

  sensors {
    uuid id PK
    text name
    text sensor_type
    numeric estimated_cost_usd
  }

  sensor_performances {
    uuid id PK
    uuid sensor_id FK
    numeric sensitivity
    numeric specificity
    numeric lod_value
    text lod_unit
  }

  papers {
    uuid id PK
    text external_id UK
    text title
    date published_at
  }

  paper_chunks {
    uuid id PK
    uuid paper_id FK
    int chunk_index
    text content
    vector embedding
  }

  protocols {
    uuid id PK
    text name
    uuid sensor_id FK
    uuid paper_id FK
    jsonb steps
    jsonb reagents
  }

  public_health_features {
    uuid id PK
    text region_code
    uuid cancer_id FK
    text feature_type
    numeric value
    int data_year
  }
```

---

## Neo4j Graph Schema

```mermaid
graph TB
  subgraph molecular [Molecular Domain]
    CT[CtDNA]
    B[Biomarker]
    B -->|OF_CLASS| CT
  end

  subgraph clinical [Clinical Domain]
    C[Cancer]
    PHF[PublicHealthFeature]
    C -->|HAS| B
    PHF -->|FOR_CANCER| C
  end

  subgraph sensor_domain [Sensor Domain]
    R[RecognitionStrategy]
    S[Sensor]
    P[Performance]
    B -->|MATCHES| R
    R -->|USES| S
    S -->|GENERATES| P
  end

  subgraph evidence [Evidence Domain]
    PA[Paper]
    PR[Protocol]
    B -->|CITED_IN| PA
    S -->|CITED_IN| PA
    PR -->|DESCRIBES| S
    PR -->|SUPPORTED_BY| PA
  end
```

---

## Indexes

### PostgreSQL

| Table | Index | Type | Purpose |
|-------|-------|------|---------|
| `ctdna` | `idx_ctdna_code` | B-tree | Lookup by class |
| `cancers` | `idx_cancers_code` | B-tree | Lookup by cancer type |
| `biomarkers` | `idx_biomarkers_ctdna_id` | B-tree | Filter by ctDNA class |
| `biomarkers` | `idx_biomarkers_gene_symbol` | Partial B-tree | Gene search |
| `biomarker_recognition_matches` | `idx_brm_score` | B-tree DESC | Top matches |
| `sensors` | `idx_sensors_type` | B-tree | Filter by sensor type |
| `sensor_performances` | `idx_sensor_performances_lod` | Partial B-tree | LOD ranking |
| `paper_chunks` | `idx_paper_chunks_embedding` | IVFFlat | RAG cosine search |
| `papers` | `idx_papers_published_at` | B-tree DESC | Recent literature |
| `public_health_features` | `idx_phf_region`, `idx_phf_cancer` | B-tree | Regional queries |
| `recommendations` | `idx_recommendations_sensor` | B-tree | Join to catalog |

### Neo4j

| Index | Target | Purpose |
|-------|--------|---------|
| Uniqueness constraints | All entity keys | Idempotent MERGE |
| `biomarker_search` | Full-text | Biomarker name search |
| `paper_search` | Full-text | Literature title search |
| `phf_region` | `PublicHealthFeature.region_code` | Regional filter |

---

## Migrations

| File | Description |
|------|-------------|
| `infra/db/migrations/postgres/001_initial_schema.sql` | Users, cases, recommendations, RAG base |
| `infra/db/migrations/postgres/002_domain_entities.sql` | Domain entities + junction tables + renames |
| `infra/db/migrations/postgres/003_seed_domain_data.sql` | Reference + relationship seed data |
| `infra/db/migrations/neo4j/001_constraints.cypher` | Constraints + indexes |
| `infra/db/migrations/neo4j/002_seed_data.cypher` | Graph seed mirroring Postgres |

### Apply (Docker)

Postgres migrations auto-apply on first `docker compose up` via `docker-entrypoint-initdb.d`.

Neo4j seeds (manual):

```bash
cat infra/db/migrations/neo4j/001_constraints.cypher | cypher-shell -u neo4j -p biosense_dev
cat infra/db/migrations/neo4j/002_seed_data.cypher   | cypher-shell -u neo4j -p biosense_dev
```

---

## ORM (SQLAlchemy 2.0)

Location: `apps/api/src/biosense/infrastructure/persistence/postgres/`

| File | Role |
|------|------|
| `base.py` | `DeclarativeBase` |
| `session.py` | Async engine + `get_db_session()` |
| `models.py` | All entity + junction ORM models |

### Usage

```python
from biosense.infrastructure.persistence.postgres.session import get_db_session
from biosense.infrastructure.persistence.postgres.models import Biomarker, Cancer
from sqlalchemy import select

async for session in get_db_session():
    result = await session.execute(
        select(Biomarker).join(Biomarker.cancers).where(Cancer.code == "lung")
    )
    biomarkers = result.scalars().all()
```

---

## Cross-Store Sync Strategy

| Store | Role | When to Query |
|-------|------|---------------|
| Postgres | Source of truth for catalog + user data | CRUD, RAG, analytics |
| Neo4j | Traversal + path discovery | "What sensors match this biomarker?" |

`graph_sync_log` table tracks Postgres UUID ↔ Neo4j node ID for idempotent sync scripts (Phase 4).

---

## Seed Data Summary

| Entity | Count |
|--------|-------|
| CtDNA classes | 4 |
| Cancers | 9 |
| Biomarkers | 7 |
| Recognition strategies | 6 |
| Sensors | 6 |
| Sensor performances | 6 |
| Papers | 4 |
| Protocols | 3 |
| Public health features | 10 |
| Cancer–Biomarker links | 8 |
| Biomarker–Recognition matches | 8 |
| Recognition–Sensor uses | 8 |
