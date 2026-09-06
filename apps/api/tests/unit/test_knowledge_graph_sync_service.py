from unittest.mock import AsyncMock, MagicMock

import pytest

from biosense.application.services.knowledge_graph_sync_service import (
    KnowledgeGraphSyncService,
    _build_biomarker_gene_edge,
    _build_biomarker_merge,
    _build_biomarker_publication_edge,
    _build_biomarker_recognition_edge,
    _build_cancer_biomarker_edge,
    _build_cancer_merge,
    _build_gene_merge,
    _build_mutation_gene_edge,
    _build_mutation_merge,
    _build_publication_merge,
    _build_recognition_merge,
    _build_sensor_merge,
    _build_sensor_recognition_edge,
    _gdc_uuid,
    _sensor_key,
)
from biosense.domain.entities.genomics import RawGdcGeneRecord, RawGdcMutationRecord

SAMPLE_GENE = RawGdcGeneRecord(
    gene_id="ENSG00000133703",
    symbol="kras",
    name="KRAS proto-oncogene, GTPase",
    biotype="protein_coding",
    source="gdc",
)

SAMPLE_MUTATION = RawGdcMutationRecord(
    ssm_id="07f33888-b319-55fa-a680-a0b924290e55",
    genomic_dna_change="chr12:g.25227241G>A",
    mutation_subtype="Single base substitution",
    gene_symbols=["KRAS", "kras"],
    amino_acid_changes=["H95Y"],
)


# -- Pure builder tests -----------------------------------------------------------


def test_build_gene_merge_normalizes_symbol() -> None:
    query, params = _build_gene_merge(SAMPLE_GENE)
    assert "MERGE (g:Gene {symbol: $symbol})" in query
    assert params["symbol"] == "KRAS"
    assert params["gene_id"] == "ENSG00000133703"
    assert params["access_level"] == "open"


def test_build_mutation_merge() -> None:
    query, params = _build_mutation_merge(SAMPLE_MUTATION)
    assert "MERGE (m:Mutation {ssm_id: $ssm_id})" in query
    assert params["ssm_id"] == SAMPLE_MUTATION.ssm_id
    assert params["change"] == "chr12:g.25227241G>A"


def test_build_mutation_gene_edge_normalizes_symbol() -> None:
    query, params = _build_mutation_gene_edge("ssm-1", "kras")
    assert "AFFECTS_GENE" in query
    assert params["symbol"] == "KRAS"
    assert params["ssm_id"] == "ssm-1"


def test_build_cancer_merge() -> None:
    query, params = _build_cancer_merge("lung", "Lung Cancer", "폐암")
    assert "MERGE (c:Cancer {code: $code})" in query
    assert params == {"code": "lung", "name_en": "Lung Cancer", "name_ko": "폐암"}


def test_build_biomarker_merge() -> None:
    query, params = _build_biomarker_merge("KRAS G12D mutation", "KRAS")
    assert "MERGE (b:Biomarker {name: $name})" in query
    assert params["gene_symbol"] == "KRAS"


def test_build_cancer_biomarker_edge() -> None:
    query, params = _build_cancer_biomarker_edge("lung", "KRAS G12D mutation")
    assert "HAS_BIOMARKER" in query
    assert params == {"code": "lung", "name": "KRAS G12D mutation"}


def test_build_biomarker_gene_edge_normalizes_symbol() -> None:
    query, params = _build_biomarker_gene_edge("KRAS G12D mutation", "kras")
    assert "INVOLVES_GENE" in query
    assert params["symbol"] == "KRAS"


def test_build_recognition_merge() -> None:
    query, params = _build_recognition_merge("dna_hybridization", "DNA Hybridization")
    assert "RecognitionMechanism" in query
    assert params == {"code": "dna_hybridization", "name": "DNA Hybridization"}


def test_build_biomarker_recognition_edge() -> None:
    query, params = _build_biomarker_recognition_edge(
        "KRAS G12D mutation", "dna_hybridization", 0.9
    )
    assert "MATCHES_RECOGNITION" in query
    assert params["score"] == 0.9


def test_build_publication_merge() -> None:
    query, params = _build_publication_merge("pmid:123", "A Paper", "pubmed")
    assert "Publication" in query
    assert params == {"external_id": "pmid:123", "title": "A Paper", "source": "pubmed"}


def test_build_biomarker_publication_edge() -> None:
    query, params = _build_biomarker_publication_edge("KRAS G12D mutation", "pmid:123")
    assert "SUPPORTED_BY" in query
    assert params == {"name": "KRAS G12D mutation", "external_id": "pmid:123"}


def test_build_sensor_merge() -> None:
    query, params = _build_sensor_merge("electrochemical:Sensor A", "Sensor A", "electrochemical")
    assert "Sensor" in query
    assert params["key"] == "electrochemical:Sensor A"


def test_build_sensor_recognition_edge() -> None:
    query, params = _build_sensor_recognition_edge(
        "electrochemical:Sensor A", "dna_hybridization", 0.93
    )
    assert "USES_RECOGNITION" in query
    assert params["efficiency"] == 0.93


def test_sensor_key() -> None:
    assert _sensor_key("electrochemical", "Sensor A") == "electrochemical:Sensor A"


def test_gdc_uuid_deterministic() -> None:
    assert _gdc_uuid("ENSG00000133703") == _gdc_uuid("ENSG00000133703")
    assert _gdc_uuid("ENSG00000133703") != _gdc_uuid("ENSG00000000000")


# -- Async smoke tests (mocked run_query, no real Neo4j/Postgres) -----------------


def _service_with_mocked_session() -> tuple[KnowledgeGraphSyncService, AsyncMock, MagicMock]:
    run_query = AsyncMock(return_value=[])
    session = MagicMock()
    session.execute = AsyncMock()
    service = KnowledgeGraphSyncService(session, run_query=run_query)
    return service, run_query, session


@pytest.mark.asyncio
async def test_ensure_schema_runs_every_constraint() -> None:
    service, run_query, _ = _service_with_mocked_session()
    await service.ensure_schema()
    from biosense.infrastructure.graph.schema import SCHEMA_CONSTRAINTS

    assert run_query.await_count == len(SCHEMA_CONSTRAINTS)


@pytest.mark.asyncio
async def test_sync_gene_writes_merge_and_logs() -> None:
    service, run_query, session = _service_with_mocked_session()
    await service.sync_gene(SAMPLE_GENE)

    run_query.assert_awaited_once()
    query, kwargs = run_query.await_args[0][0], run_query.await_args[1]
    assert "Gene" in query
    assert kwargs["symbol"] == "KRAS"
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_sync_mutation_writes_merge_and_gene_edges() -> None:
    service, run_query, session = _service_with_mocked_session()
    await service.sync_mutation(SAMPLE_MUTATION)

    # 1 mutation MERGE + 2 gene edges (KRAS, kras — both normalize to KRAS)
    assert run_query.await_count == 3
    session.execute.assert_awaited_once()
