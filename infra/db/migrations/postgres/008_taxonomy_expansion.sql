-- Taxonomy expansion for 5 strategy cards (exosomal miRNA, CTC, multi-omics, SERS, AI-NGS, CRISPR sensor)
-- Depends on: 002_domain_entities.sql, 003_seed_domain_data.sql, 007_metric_extraction.sql
--
-- NOTE: Playbook named this 007_taxonomy_expansion.sql; 007 was already used by
-- metric extraction (is_estimated / provenance columns), so this file is 008.
--
-- OUT OF SCOPE (separate issue — not a single sensor graph path):
--   "원발부위 예측 멀티모달 리포트" requires RecommendationEngineService output mode
--   that composes multiple ranked candidates (ctDNA + miRNA + imaging/clinical signals)
--   into a tissue-of-origin report. Track as Epic: multimodal-origin-report.

-- ---------------------------------------------------------------------------
-- Expand CHECK constraints
-- ---------------------------------------------------------------------------
ALTER TABLE ctdna DROP CONSTRAINT IF EXISTS ctdna_code_check;
ALTER TABLE ctdna ADD CONSTRAINT ctdna_code_check CHECK (code IN (
    'fragmentomics', 'methylation', 'mutation', 'cnv',
    'exosomal_mirna', 'ctc', 'multi_omics'
));

ALTER TABLE biomarker_cases DROP CONSTRAINT IF EXISTS biomarker_cases_ctdna_class_check;
ALTER TABLE biomarker_cases ADD CONSTRAINT biomarker_cases_ctdna_class_check CHECK (ctdna_class IN (
    'fragmentomics', 'methylation', 'mutation', 'cnv',
    'exosomal_mirna', 'ctc', 'multi_omics'
));

ALTER TABLE recognition_strategies DROP CONSTRAINT IF EXISTS recognition_strategies_code_check;
ALTER TABLE recognition_strategies ADD CONSTRAINT recognition_strategies_code_check CHECK (code IN (
    'antibody_based', 'aptamer_based',
    'molecularly_imprinted_polymer', 'dna_hybridization',
    'enzyme_linked', 'crispr_based',
    'ai_classification'
));

ALTER TABLE sensors DROP CONSTRAINT IF EXISTS sensors_sensor_type_check;
ALTER TABLE sensors ADD CONSTRAINT sensors_sensor_type_check CHECK (sensor_type IN (
    'electrochemical', 'optical', 'piezoelectric',
    'field_effect_transistor', 'lateral_flow', 'microfluidic',
    'SERS', 'AI_NGS', 'CRISPR_dedicated'
));

-- ---------------------------------------------------------------------------
-- CtDNA classes
-- ---------------------------------------------------------------------------
INSERT INTO ctdna (code, name, description) VALUES
    ('exosomal_mirna', 'Exosomal miRNA',
     'Circulating exosome-encapsulated microRNAs as liquid biopsy analytes'),
    ('ctc', 'Circulating Tumor Cell',
     'Intact circulating tumor cells and CTC-derived molecular signatures'),
    ('multi_omics', 'Multi-omics Panel',
     'Integrated DNA/RNA/protein (and fragment) panels for liquid biopsy')
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Recognition strategies (AI classification for miRNA / multi-omics panels)
-- ---------------------------------------------------------------------------
INSERT INTO recognition_strategies (code, name, description, neo4j_id) VALUES
    ('ai_classification', 'AI/ML classification',
     'Supervised or deep learning classifiers over NGS, spectral, or multi-analyte profiles',
     'rec:ai-class')
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Biomarkers
-- ---------------------------------------------------------------------------
INSERT INTO biomarkers (name, ctdna_id, gene_symbol, description, neo4j_id)
SELECT v.name, c.id, v.gene, v.descr, v.nid
FROM (VALUES
    ('miR-21',  'exosomal_mirna', 'MIR21',
     'OncomiR enriched in tumor-derived exosomes (pan-cancer)', 'bio:mir-21'),
    ('miR-141', 'exosomal_mirna', 'MIR141',
     'Exosomal miR-141 associated with prostate and epithelial cancers', 'bio:mir-141'),
    ('miR-1246','exosomal_mirna', 'MIR1246',
     'Exosomal miR-1246 linked to metastasis and therapy response', 'bio:mir-1246'),
    ('EpCAM+ CTC enumeration', 'ctc', 'EPCAM',
     'EpCAM-positive circulating tumor cell count / phenotype', 'bio:ctc-epcam'),
    ('ctDNA + protein multi-omics panel', 'multi_omics', NULL,
     'Combined somatic mutation / methylation with circulating protein markers',
     'bio:multi-dna-protein'),
    ('fragmentomics + miRNA multi-omics panel', 'multi_omics', NULL,
     'cfDNA fragment features integrated with exosomal miRNA signatures',
     'bio:multi-frag-mirna'),
    ('methylation + mutation multi-omics panel', 'multi_omics', NULL,
     'Joint methylation and mutation panel for early detection / TOOish signals',
     'bio:multi-meth-mut')
) AS v(name, ctdna_code, gene, descr, nid)
JOIN ctdna c ON c.code = v.ctdna_code
ON CONFLICT (name) DO NOTHING;

-- Cancer HAS Biomarker
INSERT INTO cancer_biomarkers (cancer_id, biomarker_id, notes)
SELECT ca.id, b.id, v.notes
FROM (VALUES
    ('lung',       'miR-21',  'Elevated in NSCLC exosomes'),
    ('colorectal', 'miR-21',  'CRC exosomal oncomiR'),
    ('breast',     'miR-21',  'Breast cancer exosomal marker'),
    ('prostate',   'miR-141', 'Prostate cancer enriched exosomal miRNA'),
    ('ovarian',    'miR-1246','Ovarian / metastatic enrichment'),
    ('lung',       'miR-1246','NSCLC metastasis-associated'),
    ('lung',       'EpCAM+ CTC enumeration', 'NSCLC CTC monitoring'),
    ('breast',     'EpCAM+ CTC enumeration', 'Metastatic breast CTC'),
    ('colorectal', 'EpCAM+ CTC enumeration', 'CRC CTC for MRD'),
    ('lung',       'ctDNA + protein multi-omics panel', 'Early detection panel'),
    ('colorectal', 'ctDNA + protein multi-omics panel', 'CRC screening adjunct'),
    ('other',      'fragmentomics + miRNA multi-omics panel', 'Pan-cancer integrative'),
    ('colorectal', 'methylation + mutation multi-omics panel', 'SEPT9 + mutation combo'),
    ('lung',       'methylation + mutation multi-omics panel', 'EGFR/meth panel')
) AS v(cancer_code, biomarker_name, notes)
JOIN cancers ca ON ca.code = v.cancer_code
JOIN biomarkers b ON b.name = v.biomarker_name
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- Sensors (new types)
-- ---------------------------------------------------------------------------
INSERT INTO sensors (name, sensor_type, description, estimated_cost_usd, neo4j_id) VALUES
    ('SERS plasmonic nanosensor', 'SERS',
     'Surface-enhanced Raman scattering optical nanosensor for liquid biopsy analytes',
     95.00, 'sen:sers'),
    ('AI-NGS liquid biopsy analyzer', 'AI_NGS',
     'NGS library prep + AI classifier for ctDNA / multi-analyte calls',
     450.00, 'sen:ai-ngs'),
    ('CRISPR-integrated biosensor', 'CRISPR_dedicated',
     'Hardware-integrated Cas12/Cas13 sensing cartridge (sensor-level CRISPR)',
     65.00, 'sen:crispr-ded')
ON CONFLICT (sensor_type, name) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Biomarker MATCHES RecognitionStrategy
-- Strategy card coverage (1–4):
--   1) ctDNA + AI NGS: existing mutation/meth biomarkers → dna_hybridization / crispr
--      plus recognition_sensor_uses → AI_NGS below
--   2) exosomal miRNA + AI classification: miR-* → ai_classification
--   3) optical/SERS: miR / CTC → aptamer or antibody → SERS
--   4) multi-omics panel: multi_omics biomarkers → ai_classification / dna_hybridization
-- ---------------------------------------------------------------------------
INSERT INTO biomarker_recognition_matches (biomarker_id, recognition_strategy_id, match_score, mechanism)
SELECT b.id, r.id, v.score, v.mech
FROM (VALUES
    -- Existing ctDNA mutation path strengthened for AI-NGS
    ('KRAS G12D mutation',  'dna_hybridization', 0.90, 'Amplicon / capture NGS input for AI calling'),
    ('EGFR L858R mutation', 'dna_hybridization', 0.93, 'Targeted NGS panels with AI variant classification'),
    ('TP53 mutation',       'dna_hybridization', 0.87, 'Hotspot capture sequencing + ML filtering'),
    ('SEPT9 methylation',   'ai_classification', 0.84, 'Methylation beta-vector ML classifier'),
    -- Exosomal miRNA + AI / SERS
    ('miR-21',  'ai_classification', 0.91, 'Exosomal miRNA expression vector classification'),
    ('miR-21',  'dna_hybridization', 0.88, 'Complementary probe capture of mature miR-21'),
    ('miR-21',  'aptamer_based',     0.82, 'RNA aptamer recognition of miR-21 duplex'),
    ('miR-141', 'ai_classification', 0.89, 'Prostate-enriched miRNA signature classifier'),
    ('miR-141', 'dna_hybridization', 0.86, 'Probe hybridization for miR-141'),
    ('miR-1246','ai_classification', 0.87, 'Metastasis-associated miRNA panel score'),
    ('miR-1246','aptamer_based',     0.80, 'Aptamer capture prior to SERS readout'),
    -- CTC
    ('EpCAM+ CTC enumeration', 'antibody_based', 0.94, 'Anti-EpCAM immunocapture of CTCs'),
    ('EpCAM+ CTC enumeration', 'ai_classification', 0.83, 'Imaging/AI morphometric CTC classification'),
    -- Multi-omics panels
    ('ctDNA + protein multi-omics panel', 'ai_classification', 0.92,
     'Late-fusion ML over mutation and protein features'),
    ('ctDNA + protein multi-omics panel', 'dna_hybridization', 0.85,
     'Targeted DNA module of multi-omics panel'),
    ('fragmentomics + miRNA multi-omics panel', 'ai_classification', 0.90,
     'Joint fragment-end and miRNA embedding classifier'),
    ('methylation + mutation multi-omics panel', 'ai_classification', 0.91,
     'Multi-modal methylation + mutation risk model'),
    ('methylation + mutation multi-omics panel', 'dna_hybridization', 0.88,
     'Bisulfite and mutation probe modules')
) AS v(biomarker_name, rec_code, score, mech)
JOIN biomarkers b ON b.name = v.biomarker_name
JOIN recognition_strategies r ON r.code = v.rec_code
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- RecognitionStrategy USES Sensor
-- ---------------------------------------------------------------------------
INSERT INTO recognition_sensor_uses (recognition_strategy_id, sensor_id, efficiency)
SELECT r.id, s.id, v.eff
FROM (VALUES
    -- ctDNA + AI NGS
    ('dna_hybridization',  'AI-NGS liquid biopsy analyzer', 0.93),
    ('ai_classification',  'AI-NGS liquid biopsy analyzer', 0.95),
    ('crispr_based',       'AI-NGS liquid biopsy analyzer', 0.80),
    -- SERS optical path
    ('aptamer_based',      'SERS plasmonic nanosensor', 0.90),
    ('dna_hybridization',  'SERS plasmonic nanosensor', 0.88),
    ('antibody_based',     'SERS plasmonic nanosensor', 0.86),
    ('ai_classification',  'SERS plasmonic nanosensor', 0.78),
    -- CRISPR dedicated sensor (distinct from crispr_based→LFA/microfluidic)
    ('crispr_based',       'CRISPR-integrated biosensor', 0.94),
    ('dna_hybridization',  'CRISPR-integrated biosensor', 0.81),
    -- CTC antibody capture can feed CRISPR cartridge / AI-NGS
    ('antibody_based',     'CRISPR-integrated biosensor', 0.75),
    ('antibody_based',     'AI-NGS liquid biopsy analyzer', 0.77)
) AS v(rec_code, sensor_name, eff)
JOIN recognition_strategies r ON r.code = v.rec_code
JOIN sensors s ON s.name = v.sensor_name
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- Sensor GENERATES Performance (literature-based estimates)
-- ---------------------------------------------------------------------------
INSERT INTO sensor_performances (
    sensor_id, sensitivity, specificity, auc, lod_value, lod_unit,
    assay_time_minutes, sample_volume, sample_volume_unit, estimated_cost_usd,
    assay_conditions, source, is_estimated, extraction_confidence, conflicting_sources
)
SELECT s.id, v.sens, v.spec, v.auc, v.lod, v.unit,
       v.assay_min, v.vol, v.vol_unit, v.cost,
       v.cond, v.src, true, v.conf, false
FROM (VALUES
    ('SERS plasmonic nanosensor',
     0.90, 0.92, 0.94, 0.02, 'ng/mL', 45.0, 20.0, 'µL', 95.00,
     'Colloidal Au/Ag SERS substrate, 785 nm excitation',
     'Literature estimate (taxonomy seed)', 0.70),
    ('AI-NGS liquid biopsy analyzer',
     0.94, 0.96, 0.97, 0.001, 'ng/mL', 720.0, 4.0, 'mL', 450.00,
     'Targeted NGS ≥30k× depth + locked ML classifier',
     'Literature estimate (taxonomy seed)', 0.72),
    ('CRISPR-integrated biosensor',
     0.91, 0.93, 0.95, 0.05, 'ng/mL', 35.0, 50.0, 'µL', 65.00,
     'RPA + Cas12a collateral cleavage in sealed cartridge',
     'Literature estimate (taxonomy seed)', 0.68)
) AS v(sensor_name, sens, spec, auc, lod, unit, assay_min, vol, vol_unit, cost, cond, src, conf)
JOIN sensors s ON s.name = v.sensor_name
WHERE NOT EXISTS (
    SELECT 1
    FROM sensor_performances sp
    WHERE sp.sensor_id = s.id
      AND sp.source = 'Literature estimate (taxonomy seed)'
);

-- ---------------------------------------------------------------------------
-- Verification queries (run manually after apply)
-- ---------------------------------------------------------------------------
-- 1) ctDNA + AI NGS:
-- SELECT b.name, r.code, s.sensor_type
-- FROM biomarkers b
-- JOIN biomarker_recognition_matches m ON m.biomarker_id = b.id
-- JOIN recognition_strategies r ON r.id = m.recognition_strategy_id
-- JOIN recognition_sensor_uses u ON u.recognition_strategy_id = r.id
-- JOIN sensors s ON s.id = u.sensor_id
-- JOIN ctdna c ON c.id = b.ctdna_id
-- WHERE c.code IN ('mutation','methylation','cnv','fragmentomics') AND s.sensor_type = 'AI_NGS';
--
-- 2) exosomal miRNA + AI classification:
-- ... WHERE c.code = 'exosomal_mirna' AND r.code = 'ai_classification';
--
-- 3) optical/SERS:
-- ... WHERE s.sensor_type = 'SERS';
--
-- 4) multi-omics panel:
-- ... WHERE c.code = 'multi_omics';
--
-- 5) tissue-of-origin multimodal report: NOT covered by graph seed — separate engine mode.
