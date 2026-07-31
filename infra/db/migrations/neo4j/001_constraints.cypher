// BioSense-GovAI Neo4j schema — constraints and indexes
// Entity labels: Cancer, Biomarker, CtDNA, RecognitionStrategy, Sensor,
//                Paper, Protocol, PublicHealthFeature, Performance
//
// Relationships:
//   (Cancer)-[:HAS]->(Biomarker)
//   (Biomarker)-[:MATCHES]->(RecognitionStrategy)
//   (RecognitionStrategy)-[:USES]->(Sensor)
//   (Sensor)-[:GENERATES]->(Performance)
//   (Biomarker)-[:OF_CLASS]->(CtDNA)
//   (Biomarker)-[:CITED_IN]->(Paper)
//   (Sensor)-[:CITED_IN]->(Paper)
//   (Protocol)-[:DESCRIBES]->(Sensor)
//   (Protocol)-[:SUPPORTED_BY]->(Paper)
//   (PublicHealthFeature)-[:FOR_CANCER]->(Cancer)

// --- Uniqueness constraints ---
CREATE CONSTRAINT cancer_code IF NOT EXISTS
FOR (c:Cancer) REQUIRE c.code IS UNIQUE;

CREATE CONSTRAINT ctdna_code IF NOT EXISTS
FOR (c:CtDNA) REQUIRE c.code IS UNIQUE;

CREATE CONSTRAINT biomarker_name IF NOT EXISTS
FOR (b:Biomarker) REQUIRE b.name IS UNIQUE;

CREATE CONSTRAINT recognition_code IF NOT EXISTS
FOR (r:RecognitionStrategy) REQUIRE r.code IS UNIQUE;

CREATE CONSTRAINT sensor_key IF NOT EXISTS
FOR (s:Sensor) REQUIRE (s.type, s.name) IS UNIQUE;

CREATE CONSTRAINT paper_external_id IF NOT EXISTS
FOR (p:Paper) REQUIRE p.external_id IS UNIQUE;

CREATE CONSTRAINT protocol_name IF NOT EXISTS
FOR (p:Protocol) REQUIRE p.name IS UNIQUE;

CREATE CONSTRAINT phf_key IF NOT EXISTS
FOR (f:PublicHealthFeature) REQUIRE (f.region_code, f.cancer_code, f.feature_type, f.data_year) IS UNIQUE;

// --- Lookup indexes ---
CREATE INDEX biomarker_gene IF NOT EXISTS FOR (b:Biomarker) ON (b.gene_symbol);
CREATE INDEX sensor_type IF NOT EXISTS FOR (s:Sensor) ON (s.type);
CREATE INDEX paper_title IF NOT EXISTS FOR (p:Paper) ON (p.title);
CREATE INDEX phf_region IF NOT EXISTS FOR (f:PublicHealthFeature) ON (f.region_code);

// --- Full-text search (optional, Neo4j 5+) ---
CREATE FULLTEXT INDEX biomarker_search IF NOT EXISTS
FOR (b:Biomarker) ON EACH [b.name, b.description];

CREATE FULLTEXT INDEX paper_search IF NOT EXISTS
FOR (p:Paper) ON EACH [p.title];
