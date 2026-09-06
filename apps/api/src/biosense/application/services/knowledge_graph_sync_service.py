"""Sync the domain graph (Postgres) and global genomic data (GDC) into Neo4j.

The recommendation engine's actual traversal (GraphRetrievalService) runs entirely in
Postgres — this service does not change that. It populates the previously-idle Neo4j
instance (see docs/architecture notes: `neo4j_id` columns and `graph_sync_log` existed
in the schema, but nothing ever wrote to Neo4j besides a health-check ping) so the
graph becomes a real, queryable knowledge graph for exploratory/global-data use cases
that don't fit the relational recommendation path — e.g. gene/mutation lookups from
NCI GDC, which have no natural home in the ctDNA-case-centric Postgres schema.

Every write method is a thin async wrapper around a pure `_build_*` function that
returns a (cypher, params) tuple — the pure functions are what's unit-tested; the
async methods only need a smoke test that they call `run_query` with that pair.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from biosense.domain.entities.genomics import RawGdcGeneRecord, RawGdcMutationRecord
from biosense.domain.services.normalization import normalize_gene_symbol
from biosense.infrastructure.graph import neo4j_client
from biosense.infrastructure.graph.schema import SCHEMA_CONSTRAINTS
from biosense.infrastructure.persistence.postgres.models import (
    Biomarker,
    BiomarkerRecognitionMatch,
    Cancer,
    GraphSyncLog,
    RecognitionSensorUse,
    RecognitionStrategy,
    Sensor,
)

logger = structlog.get_logger()

# Deterministic UUIDs for external (non-Postgres-native) records, so gdc_gene /
# gdc_mutation rows can still use graph_sync_log's UUID entity_id column.
_GDC_NAMESPACE = uuid.UUID("6f9b3f6e-1a2b-4c3d-9e8f-2a1b3c4d5e6f")

RunQuery = Callable[..., Awaitable[list[dict[str, Any]]]]


class KnowledgeGraphSyncService:
    def __init__(self, session: AsyncSession, *, run_query: RunQuery | None = None) -> None:
        self._session = session
        self._run_query = run_query or neo4j_client.run_write

    async def ensure_schema(self) -> None:
        for statement in SCHEMA_CONSTRAINTS:
            await self._run_query(statement)
        logger.info("kg_schema_ensured", constraints=len(SCHEMA_CONSTRAINTS))

    # -- GDC global genomic data --------------------------------------------------

    async def sync_gene(self, gene: RawGdcGeneRecord) -> None:
        query, params = _build_gene_merge(gene)
        await self._run_query(query, **params)
        await self._log_sync("gdc_gene", _gdc_uuid(gene.gene_id), params["symbol"])

    async def sync_mutation(self, mutation: RawGdcMutationRecord) -> None:
        query, params = _build_mutation_merge(mutation)
        await self._run_query(query, **params)
        for symbol in mutation.gene_symbols:
            edge_query, edge_params = _build_mutation_gene_edge(mutation.ssm_id, symbol)
            await self._run_query(edge_query, **edge_params)
        await self._log_sync("gdc_mutation", _gdc_uuid(mutation.ssm_id), mutation.ssm_id)

    # -- Existing Postgres domain graph -------------------------------------------

    async def sync_domain_graph(self) -> dict[str, int]:
        """Push the existing Cancer→Biomarker→Recognition→Sensor graph into Neo4j."""
        counts = {"cancers": 0, "biomarkers": 0, "sensors": 0, "publications": 0}

        cancers = (await self._session.execute(select(Cancer))).scalars().all()
        for cancer in cancers:
            query, params = _build_cancer_merge(cancer.code, cancer.name_en, cancer.name_ko)
            await self._run_query(query, **params)
            await self._log_sync("cancer", cancer.id, f"cancer:{cancer.code}")
            counts["cancers"] += 1

        biomarkers = (
            (
                await self._session.execute(
                    select(Biomarker).options(
                        selectinload(Biomarker.cancers),
                        selectinload(Biomarker.recognition_matches).selectinload(
                            BiomarkerRecognitionMatch.recognition_strategy
                        ),
                        selectinload(Biomarker.papers),
                    )
                )
            )
            .scalars()
            .unique()
            .all()
        )

        for biomarker in biomarkers:
            query, params = _build_biomarker_merge(biomarker.name, biomarker.gene_symbol)
            await self._run_query(query, **params)
            await self._log_sync("biomarker", biomarker.id, f"biomarker:{biomarker.name}")
            counts["biomarkers"] += 1

            for cancer in biomarker.cancers:
                edge_q, edge_p = _build_cancer_biomarker_edge(cancer.code, biomarker.name)
                await self._run_query(edge_q, **edge_p)

            if biomarker.gene_symbol:
                edge_q, edge_p = _build_biomarker_gene_edge(biomarker.name, biomarker.gene_symbol)
                await self._run_query(edge_q, **edge_p)

            for match in biomarker.recognition_matches:
                rec = match.recognition_strategy
                rec_q, rec_p = _build_recognition_merge(rec.code, rec.name)
                await self._run_query(rec_q, **rec_p)
                match_q, match_p = _build_biomarker_recognition_edge(
                    biomarker.name, rec.code, float(match.match_score)
                )
                await self._run_query(match_q, **match_p)

            for paper in biomarker.papers:
                pub_q, pub_p = _build_publication_merge(
                    paper.external_id, paper.title, paper.source
                )
                await self._run_query(pub_q, **pub_p)
                sup_q, sup_p = _build_biomarker_publication_edge(biomarker.name, paper.external_id)
                await self._run_query(sup_q, **sup_p)
                counts["publications"] += 1

        sensors = (await self._session.execute(select(Sensor))).scalars().all()
        for sensor in sensors:
            key = _sensor_key(sensor.sensor_type, sensor.name)
            query, params = _build_sensor_merge(key, sensor.name, sensor.sensor_type)
            await self._run_query(query, **params)
            await self._log_sync("sensor", sensor.id, key)
            counts["sensors"] += 1

        uses = (
            await self._session.execute(
                select(RecognitionSensorUse, RecognitionStrategy, Sensor)
                .join(
                    RecognitionStrategy,
                    RecognitionStrategy.id == RecognitionSensorUse.recognition_strategy_id,
                )
                .join(Sensor, Sensor.id == RecognitionSensorUse.sensor_id)
            )
        ).all()
        for use, rec, sensor in uses:
            key = _sensor_key(sensor.sensor_type, sensor.name)
            query, params = _build_sensor_recognition_edge(
                key, rec.code, float(use.efficiency) if use.efficiency is not None else None
            )
            await self._run_query(query, **params)

        logger.info("kg_domain_sync_complete", **counts)
        return counts

    async def _log_sync(self, entity_type: str, entity_id: uuid.UUID, neo4j_id: str) -> None:
        stmt = (
            pg_insert(GraphSyncLog)
            .values(entity_type=entity_type, entity_id=entity_id, neo4j_id=neo4j_id)
            .on_conflict_do_update(
                index_elements=["entity_type", "entity_id"],
                set_={"neo4j_id": neo4j_id},
            )
        )
        await self._session.execute(stmt)


def _gdc_uuid(external_key: str) -> uuid.UUID:
    return uuid.uuid5(_GDC_NAMESPACE, external_key)


def _sensor_key(sensor_type: str, name: str) -> str:
    return f"{sensor_type}:{name}"


# -- Pure Cypher builders (unit-testable without any I/O) ------------------------


def _build_gene_merge(gene: RawGdcGeneRecord) -> tuple[str, dict[str, Any]]:
    symbol = normalize_gene_symbol(gene.symbol)
    query = (
        "MERGE (g:Gene {symbol: $symbol}) "
        "SET g.gene_id = $gene_id, g.name = $name, g.biotype = $biotype, "
        "g.source = $source, g.access_level = $access_level"
    )
    params = {
        "symbol": symbol,
        "gene_id": gene.gene_id,
        "name": gene.name,
        "biotype": gene.biotype,
        "source": gene.source,
        "access_level": gene.access_level,
    }
    return query, params


def _build_mutation_merge(mutation: RawGdcMutationRecord) -> tuple[str, dict[str, Any]]:
    query = (
        "MERGE (m:Mutation {ssm_id: $ssm_id}) "
        "SET m.genomic_dna_change = $change, m.mutation_subtype = $subtype, "
        "m.source = $source, m.access_level = $access_level"
    )
    params = {
        "ssm_id": mutation.ssm_id,
        "change": mutation.genomic_dna_change,
        "subtype": mutation.mutation_subtype,
        "source": mutation.source,
        "access_level": mutation.access_level,
    }
    return query, params


def _build_mutation_gene_edge(ssm_id: str, gene_symbol: str) -> tuple[str, dict[str, Any]]:
    query = (
        "MERGE (g:Gene {symbol: $symbol}) "
        "WITH g MATCH (m:Mutation {ssm_id: $ssm_id}) "
        "MERGE (m)-[:AFFECTS_GENE]->(g)"
    )
    return query, {"symbol": normalize_gene_symbol(gene_symbol), "ssm_id": ssm_id}


def _build_cancer_merge(code: str, name_en: str, name_ko: str | None) -> tuple[str, dict[str, Any]]:
    query = "MERGE (c:Cancer {code: $code}) SET c.name_en = $name_en, c.name_ko = $name_ko"
    return query, {"code": code, "name_en": name_en, "name_ko": name_ko}


def _build_biomarker_merge(name: str, gene_symbol: str | None) -> tuple[str, dict[str, Any]]:
    query = "MERGE (b:Biomarker {name: $name}) SET b.gene_symbol = $gene_symbol"
    return query, {"name": name, "gene_symbol": gene_symbol}


def _build_cancer_biomarker_edge(
    cancer_code: str, biomarker_name: str
) -> tuple[str, dict[str, Any]]:
    query = (
        "MATCH (c:Cancer {code: $code}) MATCH (b:Biomarker {name: $name}) "
        "MERGE (c)-[:HAS_BIOMARKER]->(b)"
    )
    return query, {"code": cancer_code, "name": biomarker_name}


def _build_biomarker_gene_edge(
    biomarker_name: str, gene_symbol: str
) -> tuple[str, dict[str, Any]]:
    query = (
        "MERGE (g:Gene {symbol: $symbol}) "
        "WITH g MATCH (b:Biomarker {name: $name}) "
        "MERGE (b)-[:INVOLVES_GENE]->(g)"
    )
    return query, {"symbol": normalize_gene_symbol(gene_symbol), "name": biomarker_name}


def _build_recognition_merge(code: str, name: str) -> tuple[str, dict[str, Any]]:
    query = "MERGE (r:RecognitionMechanism {code: $code}) SET r.name = $name"
    return query, {"code": code, "name": name}


def _build_biomarker_recognition_edge(
    biomarker_name: str, recognition_code: str, match_score: float
) -> tuple[str, dict[str, Any]]:
    query = (
        "MATCH (b:Biomarker {name: $name}) MATCH (r:RecognitionMechanism {code: $code}) "
        "MERGE (b)-[m:MATCHES_RECOGNITION]->(r) SET m.match_score = $score"
    )
    return query, {"name": biomarker_name, "code": recognition_code, "score": match_score}


def _build_publication_merge(
    external_id: str, title: str, source: str
) -> tuple[str, dict[str, Any]]:
    query = (
        "MERGE (p:Publication {external_id: $external_id}) SET p.title = $title, p.source = $source"
    )
    return query, {"external_id": external_id, "title": title, "source": source}


def _build_biomarker_publication_edge(
    biomarker_name: str, external_id: str
) -> tuple[str, dict[str, Any]]:
    query = (
        "MATCH (b:Biomarker {name: $name}) MATCH (p:Publication {external_id: $external_id}) "
        "MERGE (b)-[:SUPPORTED_BY]->(p)"
    )
    return query, {"name": biomarker_name, "external_id": external_id}


def _build_sensor_merge(key: str, name: str, sensor_type: str) -> tuple[str, dict[str, Any]]:
    query = "MERGE (s:Sensor {key: $key}) SET s.name = $name, s.sensor_type = $sensor_type"
    return query, {"key": key, "name": name, "sensor_type": sensor_type}


def _build_sensor_recognition_edge(
    sensor_key: str, recognition_code: str, efficiency: float | None
) -> tuple[str, dict[str, Any]]:
    query = (
        "MATCH (s:Sensor {key: $key}) MATCH (r:RecognitionMechanism {code: $code}) "
        "MERGE (s)-[u:USES_RECOGNITION]->(r) SET u.efficiency = $efficiency"
    )
    return query, {"key": sensor_key, "code": recognition_code, "efficiency": efficiency}
