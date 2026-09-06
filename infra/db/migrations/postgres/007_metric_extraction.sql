-- Metric extraction provenance columns on sensor_performances
-- Enables paper-sourced quantitative metrics with conflict tracking

ALTER TABLE sensor_performances
    ADD COLUMN IF NOT EXISTS auc NUMERIC(5, 4)
        CHECK (auc IS NULL OR (auc BETWEEN 0 AND 1)),
    ADD COLUMN IF NOT EXISTS assay_time_minutes NUMERIC
        CHECK (assay_time_minutes IS NULL OR assay_time_minutes >= 0),
    ADD COLUMN IF NOT EXISTS sample_volume NUMERIC
        CHECK (sample_volume IS NULL OR sample_volume >= 0),
    ADD COLUMN IF NOT EXISTS sample_volume_unit TEXT,
    ADD COLUMN IF NOT EXISTS estimated_cost_usd NUMERIC
        CHECK (estimated_cost_usd IS NULL OR estimated_cost_usd >= 0),
    ADD COLUMN IF NOT EXISTS source_paper_id UUID REFERENCES papers (id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS extraction_confidence NUMERIC(5, 4)
        CHECK (extraction_confidence IS NULL OR (extraction_confidence BETWEEN 0 AND 1)),
    ADD COLUMN IF NOT EXISTS is_estimated BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS conflicting_sources BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS source_excerpt TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS uq_sensor_performances_sensor_paper
    ON sensor_performances (sensor_id, source_paper_id)
    WHERE source_paper_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sensor_performances_source_paper
    ON sensor_performances (source_paper_id)
    WHERE source_paper_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_sensor_performances_conflicting
    ON sensor_performances (sensor_id)
    WHERE conflicting_sources = true;
