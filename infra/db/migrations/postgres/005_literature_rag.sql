-- BioSense-GovAI scientific literature RAG extensions
-- Depends on: 002_domain_entities.sql (papers, paper_chunks)

ALTER TABLE papers
    ADD COLUMN IF NOT EXISTS ingestion_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (ingestion_status IN ('pending', 'processing', 'indexed', 'failed')),
    ADD COLUMN IF NOT EXISTS pdf_filename TEXT,
    ADD COLUMN IF NOT EXISTS chunk_count INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS abstract TEXT,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE INDEX IF NOT EXISTS idx_papers_ingestion_status ON papers (ingestion_status);

CREATE TABLE IF NOT EXISTS literature_ingestion_jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id        UUID NOT NULL REFERENCES papers (id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    chunks_created  INT NOT NULL DEFAULT 0,
    error_message   TEXT,
    started_at      TIMESTAMPTZ,
    finished_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lit_ingestion_paper ON literature_ingestion_jobs (paper_id);

CREATE TABLE IF NOT EXISTS rag_query_logs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text          TEXT NOT NULL,
    cancer_type         TEXT,
    biomarker_name      TEXT,
    top_k               INT NOT NULL,
    chunks_retrieved    INT NOT NULL DEFAULT 0,
    recommendations     JSONB NOT NULL DEFAULT '[]',
    citations           JSONB NOT NULL DEFAULT '[]',
    latency_ms          INT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_query_logs_created ON rag_query_logs (created_at DESC);

CREATE TABLE IF NOT EXISTS rag_evaluations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text          TEXT NOT NULL,
    precision_at_k      NUMERIC(5, 4),
    recall_at_k         NUMERIC(5, 4),
    citation_coverage   NUMERIC(5, 4),
    mrr                 NUMERIC(5, 4),
    chunks_evaluated    INT NOT NULL DEFAULT 0,
    details             JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_evaluations_created ON rag_evaluations (created_at DESC);

DROP TRIGGER IF EXISTS trg_papers_updated_at ON papers;
CREATE TRIGGER trg_papers_updated_at
    BEFORE UPDATE ON papers
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
