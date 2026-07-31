-- BioSense-GovAI domain seed data
-- Depends on: 002_domain_entities.sql

-- ---------------------------------------------------------------------------
-- CtDNA classes
-- ---------------------------------------------------------------------------
INSERT INTO ctdna (code, name, description) VALUES
    ('fragmentomics', 'Fragmentomics',
     'cfDNA fragment size and end-motif distribution patterns'),
    ('methylation', 'Methylation',
     'Tumor-derived DNA methylation signatures in circulation'),
    ('mutation', 'Mutation',
     'Somatic point mutations and indels detectable in ctDNA'),
    ('cnv', 'Copy Number Variation',
     'Amplifications and deletions in circulating tumor DNA')
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Cancers
-- ---------------------------------------------------------------------------
INSERT INTO cancers (code, name_en, name_ko, icd_code) VALUES
    ('lung',        'Lung Cancer',           '폐암',       'C34'),
    ('colorectal',  'Colorectal Cancer',     '대장암',     'C18-C20'),
    ('breast',      'Breast Cancer',         '유방암',     'C50'),
    ('liver',       'Liver Cancer',          '간암',       'C22'),
    ('stomach',     'Stomach Cancer',        '위암',       'C16'),
    ('pancreatic',  'Pancreatic Cancer',     '췌장암',     'C25'),
    ('ovarian',     'Ovarian Cancer',        '난소암',     'C56'),
    ('prostate',    'Prostate Cancer',       '전립선암',   'C61'),
    ('other',       'Other Cancers',         '기타 암',    NULL)
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Biomarkers
-- ---------------------------------------------------------------------------
INSERT INTO biomarkers (name, ctdna_id, gene_symbol, description, neo4j_id)
SELECT v.name, c.id, v.gene, v.descr, v.nid
FROM (VALUES
    ('KRAS G12D mutation',       'mutation',       'KRAS', 'Oncogenic KRAS G12D driver mutation in ctDNA',       'bio:kras-g12d'),
    ('EGFR L858R mutation',    'mutation',       'EGFR', 'EGFR tyrosine kinase domain activating mutation',      'bio:egfr-l858r'),
    ('SEPT9 methylation',      'methylation',    'SEPT9','Hypermethylated SEPT9 promoter in colorectal cancer', 'bio:sept9-meth'),
    ('Fragment length profile','fragmentomics',  NULL,   'Abnormal cfDNA fragment size distribution',           'bio:frag-len'),
    ('TP53 mutation',          'mutation',       'TP53', 'Tumor suppressor TP53 loss-of-function mutation',       'bio:tp53'),
    ('BRCA1 methylation',      'methylation',    'BRCA1','BRCA1 promoter methylation in breast/ovarian',      'bio:brca1-meth'),
    ('PIK3CA H1047R',          'mutation',       'PIK3CA','PI3K pathway activating mutation',                'bio:pik3ca')
) AS v(name, ctdna_code, gene, descr, nid)
JOIN ctdna c ON c.code = v.ctdna_code
ON CONFLICT (name) DO NOTHING;

-- Cancer HAS Biomarker
INSERT INTO cancer_biomarkers (cancer_id, biomarker_id, notes)
SELECT ca.id, b.id, v.notes
FROM (VALUES
    ('colorectal', 'KRAS G12D mutation',  'Present in ~40% of CRC'),
    ('pancreatic', 'KRAS G12D mutation',  'Present in ~90% of PDAC'),
    ('lung',       'EGFR L858R mutation', 'NSCLC adenocarcinoma driver'),
    ('colorectal', 'SEPT9 methylation',   'FDA-approved screening marker'),
    ('lung',       'Fragment length profile', 'Pan-cancer fragmentomics signal'),
    ('other',      'TP53 mutation',       'Pan-cancer tumor suppressor'),
    ('breast',     'BRCA1 methylation',   'HR-deficient breast cancer'),
    ('breast',     'PIK3CA H1047R',       'PI3K pathway in breast cancer')
) AS v(cancer_code, biomarker_name, notes)
JOIN cancers ca ON ca.code = v.cancer_code
JOIN biomarkers b ON b.name = v.biomarker_name
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- RecognitionStrategy
-- ---------------------------------------------------------------------------
INSERT INTO recognition_strategies (code, name, description, neo4j_id) VALUES
    ('aptamer_based',                 'Aptamer-based recognition',
     'Synthetic ssDNA/RNA aptamers with high affinity for ctDNA targets', 'rec:aptamer'),
    ('antibody_based',                'Antibody-based recognition',
     'Monoclonal/polyclonal antibodies against mutant peptides or proteins', 'rec:antibody'),
    ('molecularly_imprinted_polymer', 'Molecularly imprinted polymer (MIP)',
     'Synthetic polymer cavities matching target molecule shape', 'rec:mip'),
    ('dna_hybridization',             'DNA hybridization probe',
     'Sequence-specific oligonucleotide hybridization', 'rec:dna-hyb'),
    ('crispr_based',                  'CRISPR-Cas recognition',
     'Cas12/Cas13 collateral cleavage upon target recognition', 'rec:crispr'),
    ('enzyme_linked',                 'Enzyme-linked detection',
     'Horseradish peroxidase or alkaline phosphatase conjugates', 'rec:enzyme')
ON CONFLICT (code) DO NOTHING;

-- Biomarker MATCHES RecognitionStrategy
INSERT INTO biomarker_recognition_matches (biomarker_id, recognition_strategy_id, match_score, mechanism)
SELECT b.id, r.id, v.score, v.mech
FROM (VALUES
    ('KRAS G12D mutation',       'aptamer_based',                 0.92, 'Aptamer binds mutant KRAS amplicon'),
    ('EGFR L858R mutation',    'antibody_based',                0.95, 'Anti-EGFR antibody captures mutant peptide'),
    ('SEPT9 methylation',      'molecularly_imprinted_polymer', 0.89, 'MIP cavity for methylated SEPT9 motif'),
    ('SEPT9 methylation',      'dna_hybridization',             0.91, 'Bisulfite-converted probe hybridization'),
    ('Fragment length profile','dna_hybridization',             0.78, 'Size-selected cfDNA capture'),
    ('TP53 mutation',          'crispr_based',                  0.88, 'Cas12a guide RNA for TP53 hotspot'),
    ('BRCA1 methylation',      'dna_hybridization',             0.90, 'Methylation-specific probe'),
    ('PIK3CA H1047R',          'aptamer_based',                 0.86, 'Aptamer for PIK3CA mutant sequence')
) AS v(biomarker_name, rec_code, score, mech)
JOIN biomarkers b ON b.name = v.biomarker_name
JOIN recognition_strategies r ON r.code = v.rec_code
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- Sensors
-- ---------------------------------------------------------------------------
INSERT INTO sensors (name, sensor_type, description, estimated_cost_usd, neo4j_id) VALUES
    ('Gold electrode EC sensor',  'electrochemical',
     'Label-free electrochemical detection on gold microelectrode', 35.00, 'sen:gold-ec'),
    ('SPR optical biosensor',     'optical',
     'Surface plasmon resonance real-time binding analysis', 120.00, 'sen:spr'),
    ('Graphene FET sensor',       'field_effect_transistor',
     'High-sensitivity graphene field-effect transistor', 55.00, 'sen:gfet'),
    ('Lateral flow assay',        'lateral_flow',
     'Point-of-care immunochromatographic strip', 8.00, 'sen:lfa'),
    ('Microfluidic chip',         'microfluidic',
     'Integrated sample prep and detection on chip', 75.00, 'sen:micro'),
    ('QCM piezoelectric sensor',  'piezoelectric',
     'Quartz crystal microbalance mass-sensitive detection', 90.00, 'sen:qcm')
ON CONFLICT (sensor_type, name) DO NOTHING;

-- RecognitionStrategy USES Sensor
INSERT INTO recognition_sensor_uses (recognition_strategy_id, sensor_id, efficiency)
SELECT r.id, s.id, v.eff
FROM (VALUES
    ('aptamer_based',                 'Gold electrode EC sensor',  0.88),
    ('antibody_based',                'SPR optical biosensor',     0.91),
    ('molecularly_imprinted_polymer', 'Gold electrode EC sensor',  0.85),
    ('dna_hybridization',             'Microfluidic chip',         0.87),
    ('dna_hybridization',             'Graphene FET sensor',       0.89),
    ('crispr_based',                  'Lateral flow assay',        0.82),
    ('crispr_based',                  'Microfluidic chip',         0.90),
    ('enzyme_linked',                 'Lateral flow assay',        0.80)
) AS v(rec_code, sensor_name, eff)
JOIN recognition_strategies r ON r.code = v.rec_code
JOIN sensors s ON s.name = v.sensor_name
ON CONFLICT DO NOTHING;

-- Sensor GENERATES Performance
INSERT INTO sensor_performances (sensor_id, sensitivity, specificity, lod_value, lod_unit, assay_conditions, source)
SELECT s.id, v.sens, v.spec, v.lod, v.unit, v.cond, v.src
FROM (VALUES
    ('Gold electrode EC sensor',  0.92, 0.94, 0.10, 'ng/mL', 'PBS buffer, room temperature', 'Literature meta-analysis'),
    ('SPR optical biosensor',     0.95, 0.96, 0.05, 'ng/mL', 'HBS-EP+ running buffer',       'Literature meta-analysis'),
    ('Graphene FET sensor',       0.93, 0.95, 0.01, 'ng/mL', 'PBS with 1mM MgCl2',           'Literature meta-analysis'),
    ('Lateral flow assay',        0.85, 0.90, 1.00, 'ng/mL', 'Serum sample, 15 min assay',   'Literature meta-analysis'),
    ('Microfluidic chip',         0.91, 0.93, 0.20, 'ng/mL', 'Whole blood input, on-chip',   'Literature meta-analysis'),
    ('QCM piezoelectric sensor',  0.88, 0.91, 0.50, 'ng/mL', 'Aqueous phase, 25 C',          'Literature meta-analysis')
) AS v(sensor_name, sens, spec, lod, unit, cond, src)
JOIN sensors s ON s.name = v.sensor_name;

-- ---------------------------------------------------------------------------
-- Papers
-- ---------------------------------------------------------------------------
INSERT INTO papers (external_id, title, authors, published_at, source, metadata) VALUES
    ('pmid:34567890',
     'Electrochemical detection of KRAS mutations in circulating tumor DNA',
     ARRAY['Kim J', 'Park S', 'Lee H'], '2023-06-15', 'PubMed',
     '{"journal": "Biosensors and Bioelectronics", "doi": "10.1016/j.bios.2023.115234"}'),
    ('pmid:35678901',
     'Aptamer-based biosensors for circulating tumor DNA detection',
     ARRAY['Chen Y', 'Wang L'], '2024-01-20', 'PubMed',
     '{"journal": "Nature Communications", "doi": "10.1038/s41467-024-00123"}'),
    ('pmid:36789012',
     'SEPT9 methylation detection in colorectal cancer screening',
     ARRAY['Schmidt K', 'Müller R'], '2022-11-08', 'PubMed',
     '{"journal": "Clinical Chemistry", "doi": "10.1093/clinchem/hvac123"}'),
    ('pmid:37890123',
     'CRISPR-Cas12a biosensing for point-of-care ctDNA mutation detection',
     ARRAY['Zhang X', 'Liu M'], '2024-05-12', 'PubMed',
     '{"journal": "ACS Sensors", "doi": "10.1021/acssensors.4c00123"}')
ON CONFLICT (external_id) DO NOTHING;

INSERT INTO paper_biomarkers (paper_id, biomarker_id)
SELECT p.id, b.id
FROM (VALUES
    ('pmid:34567890', 'KRAS G12D mutation'),
    ('pmid:35678901', 'KRAS G12D mutation'),
    ('pmid:35678901', 'EGFR L858R mutation'),
    ('pmid:36789012', 'SEPT9 methylation'),
    ('pmid:37890123', 'TP53 mutation')
) AS v(ext_id, biomarker_name)
JOIN papers p ON p.external_id = v.ext_id
JOIN biomarkers b ON b.name = v.biomarker_name
ON CONFLICT DO NOTHING;

INSERT INTO paper_sensors (paper_id, sensor_id)
SELECT p.id, s.id
FROM (VALUES
    ('pmid:34567890', 'Gold electrode EC sensor'),
    ('pmid:35678901', 'Gold electrode EC sensor'),
    ('pmid:36789012', 'Microfluidic chip'),
    ('pmid:37890123', 'Lateral flow assay')
) AS v(ext_id, sensor_name)
JOIN papers p ON p.external_id = v.ext_id
JOIN sensors s ON s.name = v.sensor_name
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- Protocols
-- ---------------------------------------------------------------------------
INSERT INTO protocols (name, sensor_id, paper_id, steps, reagents, duration_hours, description)
SELECT v.pname, s.id, p.id, v.steps::jsonb, v.reagents::jsonb, v.hours, v.descr
FROM (VALUES
    ('KRAS EC detection protocol',
     'Gold electrode EC sensor', 'pmid:34567890',
     '["Pretreat gold electrode with plasma", "Immobilize thiolated aptamer overnight", "Block with 1% BSA", "Incubate ctDNA sample 30 min", "Measure DPV signal"]',
     '["Thiolated KRAS aptamer", "PBS buffer", "BSA", "Methylene blue redox probe"]',
     6.0, 'Electrochemical aptamer-based KRAS mutation detection'),
    ('SEPT9 methylation microfluidic protocol',
     'Microfluidic chip', 'pmid:36789012',
     '["Bisulfite convert cfDNA", "Load chip with converted sample", "Hybridize methylation probe 45 C", "Wash channels", "Fluorescence readout"]',
     '["EZ DNA methylation kit", "SEPT9 probe", "Wash buffer", "Fluorophore-conjugated streptavidin"]',
     8.0, 'Methylation-specific detection on microfluidic platform'),
    ('CRISPR-LFA TP53 protocol',
     'Lateral flow assay', 'pmid:37890123',
     '["Isothermal RPA amplification", "Cas12a cleavage reaction", "Apply to LFA strip", "Visual readout at 10 min"]',
     '["RPA primers", "Cas12a protein", "gRNA", "LFA strip", "Reaction buffer"]',
     2.5, 'Point-of-care CRISPR-based TP53 mutation detection')
) AS v(pname, sensor_name, paper_ext, steps, reagents, hours, descr)
LEFT JOIN sensors s ON s.name = v.sensor_name
LEFT JOIN papers p ON p.external_id = v.paper_ext;

-- ---------------------------------------------------------------------------
-- PublicHealthFeature (Korean regional cancer statistics)
-- ---------------------------------------------------------------------------
INSERT INTO public_health_features (region_code, region_name_ko, cancer_id, feature_type, value, unit, data_year, source)
SELECT v.rcode, v.rname, c.id, v.ftype, v.val, 'per_100k', 2023, 'KOSIS (seed)'
FROM (VALUES
    ('KR-11', '서울특별시', 'lung',       'incidence', 42.5),
    ('KR-11', '서울특별시', 'lung',       'mortality', 28.3),
    ('KR-11', '서울특별시', 'colorectal', 'incidence', 38.2),
    ('KR-11', '서울특별시', 'colorectal', 'mortality', 12.1),
    ('KR-26', '부산광역시', 'stomach',    'incidence', 45.8),
    ('KR-26', '부산광역시', 'stomach',    'mortality', 15.6),
    ('KR-41', '경기도',     'liver',      'incidence', 28.4),
    ('KR-41', '경기도',     'liver',      'mortality', 18.9),
    ('KR-11', '서울특별시', 'breast',     'incidence', 62.1),
    ('KR-11', '서울특별시', 'breast',     'mortality',  8.4)
) AS v(rcode, rname, cancer_code, ftype, val)
JOIN cancers c ON c.code = v.cancer_code
ON CONFLICT DO NOTHING;
