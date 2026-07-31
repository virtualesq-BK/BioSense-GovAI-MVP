-- BioSense-GovAI domain entity schema
-- Depends on: 001_initial_schema.sql
-- Entities: Cancer, Biomarker, CtDNA, RecognitionStrategy, Sensor,
--           Paper, Protocol, PublicHealthFeature, Performance

-- ---------------------------------------------------------------------------
-- CtDNA (molecular class taxonomy)
-- ---------------------------------------------------------------------------
CREATE TABLE ctdna (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code        TEXT NOT NULL UNIQUE
                CHECK (code IN ('fragmentomics', 'methylation', 'mutation', 'cnv')),
    name        TEXT NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ctdna_code ON ctdna (code);

-- ---------------------------------------------------------------------------
-- Cancer
-- ---------------------------------------------------------------------------
CREATE TABLE cancers (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code        TEXT NOT NULL UNIQUE
                CHECK (code IN (
                    'lung', 'colorectal', 'breast', 'liver',
                    'stomach', 'pancreatic', 'ovarian', 'prostate', 'other'
                )),
    name_en     TEXT NOT NULL,
    name_ko     TEXT,
    icd_code    TEXT,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_cancers_code ON cancers (code);

-- ---------------------------------------------------------------------------
-- Biomarker
-- ---------------------------------------------------------------------------
CREATE TABLE biomarkers (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL UNIQUE,
    ctdna_id    UUID NOT NULL REFERENCES ctdna (id),
    gene_symbol TEXT,
    description TEXT,
    neo4j_id    TEXT UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_biomarkers_ctdna_id ON biomarkers (ctdna_id);
CREATE INDEX idx_biomarkers_gene_symbol ON biomarkers (gene_symbol) WHERE gene_symbol IS NOT NULL;

-- Cancer HAS Biomarker
CREATE TABLE cancer_biomarkers (
    cancer_id    UUID NOT NULL REFERENCES cancers (id) ON DELETE CASCADE,
    biomarker_id UUID NOT NULL REFERENCES biomarkers (id) ON DELETE CASCADE,
    notes        TEXT,
    PRIMARY KEY (cancer_id, biomarker_id)
);

CREATE INDEX idx_cancer_biomarkers_biomarker ON cancer_biomarkers (biomarker_id);

-- ---------------------------------------------------------------------------
-- RecognitionStrategy
-- ---------------------------------------------------------------------------
CREATE TABLE recognition_strategies (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code        TEXT NOT NULL UNIQUE
                CHECK (code IN (
                    'antibody_based', 'aptamer_based',
                    'molecularly_imprinted_polymer', 'dna_hybridization',
                    'enzyme_linked', 'crispr_based'
                )),
    name        TEXT NOT NULL,
    description TEXT,
    neo4j_id    TEXT UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_recognition_strategies_code ON recognition_strategies (code);

-- Biomarker MATCHES RecognitionStrategy
CREATE TABLE biomarker_recognition_matches (
    biomarker_id             UUID NOT NULL REFERENCES biomarkers (id) ON DELETE CASCADE,
    recognition_strategy_id  UUID NOT NULL REFERENCES recognition_strategies (id) ON DELETE CASCADE,
    match_score              NUMERIC(5, 4) NOT NULL CHECK (match_score BETWEEN 0 AND 1),
    mechanism                TEXT,
    PRIMARY KEY (biomarker_id, recognition_strategy_id)
);

CREATE INDEX idx_brm_recognition ON biomarker_recognition_matches (recognition_strategy_id);
CREATE INDEX idx_brm_score ON biomarker_recognition_matches (match_score DESC);

-- ---------------------------------------------------------------------------
-- Sensor
-- ---------------------------------------------------------------------------
CREATE TABLE sensors (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name               TEXT NOT NULL,
    sensor_type        TEXT NOT NULL
                       CHECK (sensor_type IN (
                           'electrochemical', 'optical', 'piezoelectric',
                           'field_effect_transistor', 'lateral_flow', 'microfluidic'
                       )),
    description        TEXT,
    estimated_cost_usd NUMERIC(10, 2) CHECK (estimated_cost_usd >= 0),
    neo4j_id           TEXT UNIQUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (sensor_type, name)
);

CREATE INDEX idx_sensors_type ON sensors (sensor_type);

-- RecognitionStrategy USES Sensor
CREATE TABLE recognition_sensor_uses (
    recognition_strategy_id UUID NOT NULL REFERENCES recognition_strategies (id) ON DELETE CASCADE,
    sensor_id               UUID NOT NULL REFERENCES sensors (id) ON DELETE CASCADE,
    efficiency              NUMERIC(5, 4) CHECK (efficiency BETWEEN 0 AND 1),
    PRIMARY KEY (recognition_strategy_id, sensor_id)
);

CREATE INDEX idx_rsu_sensor ON recognition_sensor_uses (sensor_id);

-- ---------------------------------------------------------------------------
-- Performance (Sensor GENERATES Performance)
-- ---------------------------------------------------------------------------
CREATE TABLE sensor_performances (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_id        UUID NOT NULL REFERENCES sensors (id) ON DELETE CASCADE,
    sensitivity      NUMERIC(5, 4) CHECK (sensitivity BETWEEN 0 AND 1),
    specificity      NUMERIC(5, 4) CHECK (specificity BETWEEN 0 AND 1),
    lod_value        NUMERIC CHECK (lod_value >= 0),
    lod_unit         TEXT,
    assay_conditions TEXT,
    source           TEXT,
    measured_at      DATE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sensor_performances_sensor ON sensor_performances (sensor_id);
CREATE INDEX idx_sensor_performances_lod ON sensor_performances (lod_value)
    WHERE lod_value IS NOT NULL;

-- ---------------------------------------------------------------------------
-- Paper (canonical literature; migrates from literature_documents)
-- ---------------------------------------------------------------------------
ALTER TABLE literature_documents RENAME TO papers;

ALTER INDEX literature_documents_external_id_key
    RENAME TO papers_external_id_key;

ALTER TABLE literature_chunks RENAME COLUMN document_id TO paper_id;
ALTER TABLE literature_chunks RENAME TO paper_chunks;

ALTER INDEX literature_chunks_document_id_chunk_index_key
    RENAME TO paper_chunks_paper_id_chunk_index_key;
ALTER INDEX idx_literature_chunks_document
    RENAME TO idx_paper_chunks_paper;
ALTER INDEX idx_literature_chunks_embedding
    RENAME TO idx_paper_chunks_embedding;

ALTER TABLE paper_chunks
    RENAME CONSTRAINT literature_chunks_document_id_fkey
    TO paper_chunks_paper_id_fkey;

-- Paper association tables
CREATE TABLE paper_biomarkers (
    paper_id     UUID NOT NULL REFERENCES papers (id) ON DELETE CASCADE,
    biomarker_id UUID NOT NULL REFERENCES biomarkers (id) ON DELETE CASCADE,
    PRIMARY KEY (paper_id, biomarker_id)
);

CREATE TABLE paper_sensors (
    paper_id  UUID NOT NULL REFERENCES papers (id) ON DELETE CASCADE,
    sensor_id UUID NOT NULL REFERENCES sensors (id) ON DELETE CASCADE,
    PRIMARY KEY (paper_id, sensor_id)
);

CREATE INDEX idx_paper_biomarkers_biomarker ON paper_biomarkers (biomarker_id);
CREATE INDEX idx_paper_sensors_sensor ON paper_sensors (sensor_id);
CREATE INDEX idx_papers_published_at ON papers (published_at DESC);
CREATE INDEX idx_papers_source ON papers (source);

-- ---------------------------------------------------------------------------
-- Protocol
-- ---------------------------------------------------------------------------
CREATE TABLE protocols (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    sensor_id       UUID REFERENCES sensors (id) ON DELETE SET NULL,
    paper_id        UUID REFERENCES papers (id) ON DELETE SET NULL,
    steps           JSONB NOT NULL DEFAULT '[]',
    reagents        JSONB NOT NULL DEFAULT '[]',
    duration_hours  NUMERIC(8, 2) CHECK (duration_hours >= 0),
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_protocols_sensor ON protocols (sensor_id);
CREATE INDEX idx_protocols_paper ON protocols (paper_id);

-- ---------------------------------------------------------------------------
-- PublicHealthFeature
-- ---------------------------------------------------------------------------
CREATE TABLE public_health_features (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    region_code   TEXT NOT NULL,
    region_name_ko TEXT,
    cancer_id     UUID NOT NULL REFERENCES cancers (id),
    feature_type  TEXT NOT NULL
                  CHECK (feature_type IN ('incidence', 'mortality', 'prevalence', 'survival_5yr')),
    value         NUMERIC NOT NULL,
    unit          TEXT NOT NULL DEFAULT 'per_100k',
    data_year     INT NOT NULL,
    source        TEXT NOT NULL,
    fetched_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (region_code, cancer_id, feature_type, data_year)
);

CREATE INDEX idx_phf_region ON public_health_features (region_code);
CREATE INDEX idx_phf_cancer ON public_health_features (cancer_id);
CREATE INDEX idx_phf_feature_type ON public_health_features (feature_type);
CREATE INDEX idx_phf_year ON public_health_features (data_year DESC);

-- ---------------------------------------------------------------------------
-- Link user cases to domain catalog (optional FK enrichment)
-- ---------------------------------------------------------------------------
ALTER TABLE biomarker_cases
    ADD COLUMN cancer_id UUID REFERENCES cancers (id),
    ADD COLUMN biomarker_id UUID REFERENCES biomarkers (id);

CREATE INDEX idx_biomarker_cases_cancer ON biomarker_cases (cancer_id);
CREATE INDEX idx_biomarker_cases_biomarker ON biomarker_cases (biomarker_id);

-- Link recommendations to catalog entities
ALTER TABLE recommendations
    ADD COLUMN sensor_id UUID REFERENCES sensors (id),
    ADD COLUMN recognition_strategy_id UUID REFERENCES recognition_strategies (id),
    ADD COLUMN protocol_id UUID REFERENCES protocols (id);

CREATE INDEX idx_recommendations_sensor ON recommendations (sensor_id);
CREATE INDEX idx_recommendations_recognition ON recommendations (recognition_strategy_id);

-- ---------------------------------------------------------------------------
-- Neo4j sync tracking (optional, low-cost idempotency)
-- ---------------------------------------------------------------------------
CREATE TABLE graph_sync_log (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type TEXT NOT NULL,
    entity_id   UUID NOT NULL,
    neo4j_id    TEXT NOT NULL,
    synced_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_type, entity_id)
);

CREATE INDEX idx_graph_sync_neo4j ON graph_sync_log (neo4j_id);
