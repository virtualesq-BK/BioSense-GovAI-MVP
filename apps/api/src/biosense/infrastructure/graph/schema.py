"""Neo4j schema: uniqueness constraints for every node label the knowledge graph uses.

Node labels and the relationships between them:

    Cancer -[:HAS_BIOMARKER]-> Biomarker
    Biomarker -[:INVOLVES_GENE]-> Gene
    Mutation -[:AFFECTS_GENE]-> Gene
    Biomarker -[:MATCHES_RECOGNITION {match_score}]-> RecognitionMechanism
    Sensor -[:USES_RECOGNITION {efficiency}]-> RecognitionMechanism
    Biomarker -[:SUPPORTED_BY]-> Publication
    GenomicProject -[:STUDIES_SITE]-> AnatomicSite  (from GDC primary_site, not yet wired)

All `CREATE CONSTRAINT ... IF NOT EXISTS` — safe to run repeatedly (idempotent schema
migration, mirroring the `ON CONFLICT DO NOTHING` convention used in the Postgres SQL
migrations).
"""

from __future__ import annotations

SCHEMA_CONSTRAINTS: tuple[str, ...] = (
    "CREATE CONSTRAINT cancer_code IF NOT EXISTS FOR (c:Cancer) REQUIRE c.code IS UNIQUE",
    "CREATE CONSTRAINT biomarker_name IF NOT EXISTS FOR (b:Biomarker) REQUIRE b.name IS UNIQUE",
    "CREATE CONSTRAINT gene_symbol IF NOT EXISTS FOR (g:Gene) REQUIRE g.symbol IS UNIQUE",
    "CREATE CONSTRAINT mutation_ssm_id IF NOT EXISTS FOR (m:Mutation) REQUIRE m.ssm_id IS UNIQUE",
    (
        "CREATE CONSTRAINT recognition_code IF NOT EXISTS "
        "FOR (r:RecognitionMechanism) REQUIRE r.code IS UNIQUE"
    ),
    "CREATE CONSTRAINT sensor_key IF NOT EXISTS FOR (s:Sensor) REQUIRE s.key IS UNIQUE",
    (
        "CREATE CONSTRAINT publication_external_id IF NOT EXISTS "
        "FOR (p:Publication) REQUIRE p.external_id IS UNIQUE"
    ),
    "CREATE CONSTRAINT country_code IF NOT EXISTS FOR (c:Country) REQUIRE c.code IS UNIQUE",
    (
        "CREATE CONSTRAINT genomic_project_id IF NOT EXISTS "
        "FOR (p:GenomicProject) REQUIRE p.project_id IS UNIQUE"
    ),
)
