-- BioSense-GovAI PostgreSQL initial schema
-- Requires: PostgreSQL 16+ with pgvector

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------------
-- Users (synced from Clerk)
-- ---------------------------------------------------------------------------
CREATE TABLE users (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clerk_id   TEXT UNIQUE NOT NULL,
    email      TEXT NOT NULL,
    org_name   TEXT,
    role       TEXT NOT NULL DEFAULT 'researcher'
               CHECK (role IN ('researcher', 'startup', 'enterprise', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_clerk_id ON users (clerk_id);

-- ---------------------------------------------------------------------------
-- Biomarker input cases
-- ---------------------------------------------------------------------------
CREATE TABLE biomarker_cases (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    cancer_type TEXT NOT NULL
                CHECK (cancer_type IN (
                    'lung', 'colorectal', 'breast', 'liver',
                    'stomach', 'pancreatic', 'ovarian', 'prostate', 'other'
                )),
    ctdna_class TEXT NOT NULL
                CHECK (ctdna_class IN (
                    'fragmentomics', 'methylation', 'mutation', 'cnv'
                )),
    patient_age INT NOT NULL CHECK (patient_age BETWEEN 0 AND 120),
    region_code TEXT NOT NULL,
    notes       TEXT,
    status      TEXT NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft', 'submitted', 'recommended')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_biomarker_cases_user_id ON biomarker_cases (user_id);
CREATE INDEX idx_biomarker_cases_status ON biomarker_cases (status);

-- ---------------------------------------------------------------------------
-- Biosensor recommendations
-- ---------------------------------------------------------------------------
CREATE TABLE recommendations (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    biomarker_case_id     UUID NOT NULL REFERENCES biomarker_cases (id) ON DELETE CASCADE,
    rank                  INT NOT NULL CHECK (rank >= 1),
    sensor_type           TEXT NOT NULL,
    recognition_strategy  TEXT NOT NULL,
    expected_sensitivity  NUMERIC(5, 4) CHECK (expected_sensitivity BETWEEN 0 AND 1),
    expected_specificity  NUMERIC(5, 4) CHECK (expected_specificity BETWEEN 0 AND 1),
    expected_lod_value    NUMERIC CHECK (expected_lod_value >= 0),
    expected_lod_unit     TEXT,
    estimated_cost_usd    NUMERIC(10, 2) CHECK (estimated_cost_usd >= 0),
    experimental_protocol JSONB NOT NULL DEFAULT '{}',
    confidence_score      NUMERIC(5, 4) CHECK (confidence_score BETWEEN 0 AND 1),
    evidence              JSONB NOT NULL DEFAULT '{}',
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (biomarker_case_id, rank)
);

CREATE INDEX idx_recommendations_case_id ON recommendations (biomarker_case_id);

-- ---------------------------------------------------------------------------
-- Korean public health statistics cache
-- ---------------------------------------------------------------------------
CREATE TABLE public_health_stats (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    region_code     TEXT NOT NULL,
    cancer_type     TEXT NOT NULL,
    incidence_rate  NUMERIC,
    mortality_rate  NUMERIC,
    data_year       INT NOT NULL,
    source          TEXT NOT NULL,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (region_code, cancer_type, data_year)
);

CREATE INDEX idx_public_health_region ON public_health_stats (region_code);

-- ---------------------------------------------------------------------------
-- RAG literature store
-- ---------------------------------------------------------------------------
CREATE TABLE literature_documents (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id  TEXT UNIQUE NOT NULL,
    title        TEXT NOT NULL,
    authors      TEXT[],
    published_at DATE,
    source       TEXT NOT NULL,
    metadata     JSONB NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE literature_chunks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES literature_documents (id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(1536),
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX idx_literature_chunks_document ON literature_chunks (document_id);
CREATE INDEX idx_literature_chunks_embedding ON literature_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ---------------------------------------------------------------------------
-- Updated-at trigger
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_biomarker_cases_updated_at
    BEFORE UPDATE ON biomarker_cases
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
