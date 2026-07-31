-- BioSense-GovAI public data ingestion pipeline tables
-- Depends on: 002_domain_entities.sql

-- ---------------------------------------------------------------------------
-- Ingestion job monitoring
-- ---------------------------------------------------------------------------
CREATE TABLE ingestion_jobs (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type          TEXT NOT NULL
                      CHECK (job_type IN ('kdca_cancer', 'kosis_cancer', 'full_sync')),
    status            TEXT NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    source            TEXT NOT NULL,
    records_extracted INT NOT NULL DEFAULT 0,
    records_transformed INT NOT NULL DEFAULT 0,
    records_embedded  INT NOT NULL DEFAULT 0,
    records_stored    INT NOT NULL DEFAULT 0,
    error_message     TEXT,
    metadata          JSONB NOT NULL DEFAULT '{}',
    started_at        TIMESTAMPTZ,
    finished_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ingestion_jobs_status ON ingestion_jobs (status);
CREATE INDEX idx_ingestion_jobs_type_created ON ingestion_jobs (job_type, created_at DESC);

-- ---------------------------------------------------------------------------
-- HTTP response cache (Extract stage)
-- ---------------------------------------------------------------------------
CREATE TABLE ingestion_cache (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key   TEXT NOT NULL UNIQUE,
    source      TEXT NOT NULL CHECK (source IN ('KDCA', 'KOSIS', 'SEED')),
    payload     JSONB NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ingestion_cache_expires ON ingestion_cache (expires_at);
CREATE INDEX idx_ingestion_cache_source ON ingestion_cache (source);

-- ---------------------------------------------------------------------------
-- Vectorized public data documents (Embed + Store for RAG)
-- ---------------------------------------------------------------------------
CREATE TABLE public_data_documents (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_key TEXT NOT NULL UNIQUE,
    source       TEXT NOT NULL,
    title        TEXT NOT NULL,
    content      TEXT NOT NULL,
    metadata     JSONB NOT NULL DEFAULT '{}',
    data_year    INT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE public_data_chunks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES public_data_documents (id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(1536),
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX idx_public_data_docs_source ON public_data_documents (source);
CREATE INDEX idx_public_data_docs_year ON public_data_documents (data_year DESC);
CREATE INDEX idx_public_data_chunks_doc ON public_data_chunks (document_id);
CREATE INDEX idx_public_data_chunks_embedding ON public_data_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

CREATE TRIGGER trg_public_data_documents_updated_at
    BEFORE UPDATE ON public_data_documents
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
