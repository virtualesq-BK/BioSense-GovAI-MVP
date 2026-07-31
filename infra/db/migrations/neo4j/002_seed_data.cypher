// BioSense-GovAI Neo4j seed data
// Mirrors postgres/003_seed_domain_data.sql

// --- CtDNA ---
UNWIND [
  {code: 'fragmentomics', name: 'Fragmentomics', desc: 'cfDNA fragment size patterns'},
  {code: 'methylation',   name: 'Methylation',   desc: 'Tumor methylation signatures'},
  {code: 'mutation',      name: 'Mutation',      desc: 'Somatic mutations in ctDNA'},
  {code: 'cnv',           name: 'CNV',           desc: 'Copy number variations'}
] AS row
MERGE (c:CtDNA {code: row.code})
SET c.name = row.name, c.description = row.desc;

// --- Cancer ---
UNWIND [
  {code: 'lung', name_en: 'Lung Cancer', name_ko: '폐암'},
  {code: 'colorectal', name_en: 'Colorectal Cancer', name_ko: '대장암'},
  {code: 'breast', name_en: 'Breast Cancer', name_ko: '유방암'},
  {code: 'liver', name_en: 'Liver Cancer', name_ko: '간암'},
  {code: 'stomach', name_en: 'Stomach Cancer', name_ko: '위암'},
  {code: 'pancreatic', name_en: 'Pancreatic Cancer', name_ko: '췌장암'}
] AS row
MERGE (c:Cancer {code: row.code})
SET c.name_en = row.name_en, c.name_ko = row.name_ko;

// --- Biomarker + OF_CLASS + HAS ---
MERGE (b1:Biomarker {name: 'KRAS G12D mutation'})
SET b1.gene_symbol = 'KRAS', b1.description = 'Oncogenic KRAS G12D driver mutation';
MATCH (ct:CtDNA {code: 'mutation'}), (b:Biomarker {name: 'KRAS G12D mutation'})
MERGE (b)-[:OF_CLASS]->(ct);
MATCH (c:Cancer {code: 'colorectal'}), (b:Biomarker {name: 'KRAS G12D mutation'})
MERGE (c)-[:HAS {notes: 'Present in ~40% of CRC'}]->(b);
MATCH (c:Cancer {code: 'pancreatic'}), (b:Biomarker {name: 'KRAS G12D mutation'})
MERGE (c)-[:HAS {notes: 'Present in ~90% of PDAC'}]->(b);

MERGE (b2:Biomarker {name: 'EGFR L858R mutation'})
SET b2.gene_symbol = 'EGFR', b2.description = 'EGFR activating mutation';
MATCH (ct:CtDNA {code: 'mutation'}), (b:Biomarker {name: 'EGFR L858R mutation'})
MERGE (b)-[:OF_CLASS]->(ct);
MATCH (c:Cancer {code: 'lung'}), (b:Biomarker {name: 'EGFR L858R mutation'})
MERGE (c)-[:HAS]->(b);

MERGE (b3:Biomarker {name: 'SEPT9 methylation'})
SET b3.gene_symbol = 'SEPT9', b3.description = 'Methylated SEPT9 promoter';
MATCH (ct:CtDNA {code: 'methylation'}), (b:Biomarker {name: 'SEPT9 methylation'})
MERGE (b)-[:OF_CLASS]->(ct);
MATCH (c:Cancer {code: 'colorectal'}), (b:Biomarker {name: 'SEPT9 methylation'})
MERGE (c)-[:HAS]->(b);

MERGE (b4:Biomarker {name: 'TP53 mutation'})
SET b4.gene_symbol = 'TP53', b4.description = 'Pan-cancer tumor suppressor';
MATCH (ct:CtDNA {code: 'mutation'}), (b:Biomarker {name: 'TP53 mutation'})
MERGE (b)-[:OF_CLASS]->(ct);

// --- RecognitionStrategy ---
MERGE (r1:RecognitionStrategy {code: 'aptamer_based'})
SET r1.name = 'Aptamer-based recognition';
MERGE (r2:RecognitionStrategy {code: 'antibody_based'})
SET r2.name = 'Antibody-based recognition';
MERGE (r3:RecognitionStrategy {code: 'molecularly_imprinted_polymer'})
SET r3.name = 'MIP recognition';
MERGE (r4:RecognitionStrategy {code: 'dna_hybridization'})
SET r4.name = 'DNA hybridization probe';
MERGE (r5:RecognitionStrategy {code: 'crispr_based'})
SET r5.name = 'CRISPR-Cas recognition';

// Biomarker MATCHES RecognitionStrategy
MATCH (b:Biomarker {name: 'KRAS G12D mutation'}), (r:RecognitionStrategy {code: 'aptamer_based'})
MERGE (b)-[:MATCHES {score: 0.92, mechanism: 'Aptamer binds mutant KRAS amplicon'}]->(r);
MATCH (b:Biomarker {name: 'EGFR L858R mutation'}), (r:RecognitionStrategy {code: 'antibody_based'})
MERGE (b)-[:MATCHES {score: 0.95}]->(r);
MATCH (b:Biomarker {name: 'SEPT9 methylation'}), (r:RecognitionStrategy {code: 'molecularly_imprinted_polymer'})
MERGE (b)-[:MATCHES {score: 0.89}]->(r);
MATCH (b:Biomarker {name: 'SEPT9 methylation'}), (r:RecognitionStrategy {code: 'dna_hybridization'})
MERGE (b)-[:MATCHES {score: 0.91}]->(r);
MATCH (b:Biomarker {name: 'TP53 mutation'}), (r:RecognitionStrategy {code: 'crispr_based'})
MERGE (b)-[:MATCHES {score: 0.88}]->(r);

// --- Sensor ---
MERGE (s1:Sensor {name: 'Gold electrode EC sensor', type: 'electrochemical'})
SET s1.estimated_cost_usd = 35.0;
MERGE (s2:Sensor {name: 'SPR optical biosensor', type: 'optical'})
SET s2.estimated_cost_usd = 120.0;
MERGE (s3:Sensor {name: 'Graphene FET sensor', type: 'field_effect_transistor'})
SET s3.estimated_cost_usd = 55.0;
MERGE (s4:Sensor {name: 'Lateral flow assay', type: 'lateral_flow'})
SET s4.estimated_cost_usd = 8.0;
MERGE (s5:Sensor {name: 'Microfluidic chip', type: 'microfluidic'})
SET s5.estimated_cost_usd = 75.0;

// RecognitionStrategy USES Sensor
MATCH (r:RecognitionStrategy {code: 'aptamer_based'}), (s:Sensor {name: 'Gold electrode EC sensor'})
MERGE (r)-[:USES {efficiency: 0.88}]->(s);
MATCH (r:RecognitionStrategy {code: 'antibody_based'}), (s:Sensor {name: 'SPR optical biosensor'})
MERGE (r)-[:USES {efficiency: 0.91}]->(s);
MATCH (r:RecognitionStrategy {code: 'dna_hybridization'}), (s:Sensor {name: 'Microfluidic chip'})
MERGE (r)-[:USES {efficiency: 0.87}]->(s);
MATCH (r:RecognitionStrategy {code: 'crispr_based'}), (s:Sensor {name: 'Lateral flow assay'})
MERGE (r)-[:USES {efficiency: 0.82}]->(s);

// Sensor GENERATES Performance
MERGE (p1:Performance {id: 'perf:gold-ec-1'})
SET p1.sensitivity = 0.92, p1.specificity = 0.94, p1.lod_value = 0.1, p1.lod_unit = 'ng/mL';
MATCH (s:Sensor {name: 'Gold electrode EC sensor'}), (p:Performance {id: 'perf:gold-ec-1'})
MERGE (s)-[:GENERATES]->(p);

MERGE (p2:Performance {id: 'perf:spr-1'})
SET p2.sensitivity = 0.95, p2.specificity = 0.96, p2.lod_value = 0.05, p2.lod_unit = 'ng/mL';
MATCH (s:Sensor {name: 'SPR optical biosensor'}), (p:Performance {id: 'perf:spr-1'})
MERGE (s)-[:GENERATES]->(p);

MERGE (p3:Performance {id: 'perf:micro-1'})
SET p3.sensitivity = 0.91, p3.specificity = 0.93, p3.lod_value = 0.2, p3.lod_unit = 'ng/mL';
MATCH (s:Sensor {name: 'Microfluidic chip'}), (p:Performance {id: 'perf:micro-1'})
MERGE (s)-[:GENERATES]->(p);

MERGE (p4:Performance {id: 'perf:lfa-1'})
SET p4.sensitivity = 0.85, p4.specificity = 0.90, p4.lod_value = 1.0, p4.lod_unit = 'ng/mL';
MATCH (s:Sensor {name: 'Lateral flow assay'}), (p:Performance {id: 'perf:lfa-1'})
MERGE (s)-[:GENERATES]->(p);

// --- Paper ---
MERGE (pa1:Paper {external_id: 'pmid:34567890'})
SET pa1.title = 'Electrochemical detection of KRAS mutations in ctDNA', pa1.year = 2023;
MERGE (pa2:Paper {external_id: 'pmid:35678901'})
SET pa2.title = 'Aptamer-based biosensors for circulating tumor DNA', pa2.year = 2024;
MERGE (pa3:Paper {external_id: 'pmid:36789012'})
SET pa3.title = 'SEPT9 methylation detection in colorectal cancer screening', pa3.year = 2022;

MATCH (b:Biomarker {name: 'KRAS G12D mutation'}), (p:Paper {external_id: 'pmid:34567890'})
MERGE (b)-[:CITED_IN]->(p);
MATCH (s:Sensor {name: 'Gold electrode EC sensor'}), (p:Paper {external_id: 'pmid:34567890'})
MERGE (s)-[:CITED_IN]->(p);
MATCH (b:Biomarker {name: 'SEPT9 methylation'}), (p:Paper {external_id: 'pmid:36789012'})
MERGE (b)-[:CITED_IN]->(p);

// --- Protocol ---
MERGE (pr1:Protocol {name: 'KRAS EC detection protocol'})
SET pr1.duration_hours = 6.0;
MATCH (pr:Protocol {name: 'KRAS EC detection protocol'}), (s:Sensor {name: 'Gold electrode EC sensor'})
MERGE (pr)-[:DESCRIBES]->(s);
MATCH (pr:Protocol {name: 'KRAS EC detection protocol'}), (p:Paper {external_id: 'pmid:34567890'})
MERGE (pr)-[:SUPPORTED_BY]->(p);

MERGE (pr2:Protocol {name: 'SEPT9 methylation microfluidic protocol'})
SET pr2.duration_hours = 8.0;
MATCH (pr:Protocol {name: 'SEPT9 methylation microfluidic protocol'}), (s:Sensor {name: 'Microfluidic chip'})
MERGE (pr)-[:DESCRIBES]->(s);

// --- PublicHealthFeature ---
MERGE (f1:PublicHealthFeature {region_code: 'KR-11', cancer_code: 'lung', feature_type: 'incidence', data_year: 2023})
SET f1.region_name_ko = '서울특별시', f1.value = 42.5, f1.unit = 'per_100k', f1.source = 'KOSIS';
MATCH (f:PublicHealthFeature {region_code: 'KR-11', cancer_code: 'lung', feature_type: 'incidence', data_year: 2023}),
      (c:Cancer {code: 'lung'})
MERGE (f)-[:FOR_CANCER]->(c);

MERGE (f2:PublicHealthFeature {region_code: 'KR-11', cancer_code: 'colorectal', feature_type: 'incidence', data_year: 2023})
SET f2.region_name_ko = '서울특별시', f2.value = 38.2, f2.unit = 'per_100k', f2.source = 'KOSIS';
MATCH (f:PublicHealthFeature {region_code: 'KR-11', cancer_code: 'colorectal', feature_type: 'incidence', data_year: 2023}),
      (c:Cancer {code: 'colorectal'})
MERGE (f)-[:FOR_CANCER]->(c);

MERGE (f3:PublicHealthFeature {region_code: 'KR-26', cancer_code: 'stomach', feature_type: 'incidence', data_year: 2023})
SET f3.region_name_ko = '부산광역시', f3.value = 45.8, f3.unit = 'per_100k', f3.source = 'KOSIS';
MATCH (f:PublicHealthFeature {region_code: 'KR-26', cancer_code: 'stomach', feature_type: 'incidence', data_year: 2023}),
      (c:Cancer {code: 'stomach'})
MERGE (f)-[:FOR_CANCER]->(c);
