from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from biosense.infrastructure.external.gdc_client import (
    GdcClient,
    _parse_gene,
    _parse_mutation,
    _parse_project,
)

SAMPLE_PROJECTS = {
    "data": {
        "hits": [
            {
                "id": "TCGA-LUAD",
                "project_id": "TCGA-LUAD",
                "name": "Lung Adenocarcinoma",
                "primary_site": ["Bronchus and lung"],
                "disease_type": ["Adenomas and Adenocarcinomas"],
                "summary": {"case_count": 585},
            }
        ]
    }
}

SAMPLE_GENES = {
    "data": {
        "hits": [
            {
                "id": "ENSG00000133703",
                "gene_id": "ENSG00000133703",
                "symbol": "KRAS",
                "name": "KRAS proto-oncogene, GTPase",
                "biotype": "protein_coding",
            }
        ]
    }
}

SAMPLE_SSMS = {
    "data": {
        "hits": [
            {
                "id": "07f33888-b319-55fa-a680-a0b924290e55",
                "ssm_id": "07f33888-b319-55fa-a680-a0b924290e55",
                "genomic_dna_change": "chr12:g.25227241G>A",
                "mutation_subtype": "Single base substitution",
                "consequence": [
                    {"transcript": {"gene": {"symbol": "KRAS"}, "aa_change": "H95Y"}},
                    {"transcript": {"gene": {"symbol": "KRAS"}}},
                ],
            }
        ]
    }
}


def test_parse_project() -> None:
    record = _parse_project(SAMPLE_PROJECTS["data"]["hits"][0])
    assert record.project_id == "TCGA-LUAD"
    assert record.primary_sites == ["Bronchus and lung"]
    assert record.case_count == 585
    assert record.source == "gdc"
    assert record.access_level == "open"


def test_parse_gene() -> None:
    record = _parse_gene(SAMPLE_GENES["data"]["hits"][0])
    assert record.symbol == "KRAS"
    assert record.gene_id == "ENSG00000133703"
    assert record.biotype == "protein_coding"


def test_parse_mutation_deduplicates_gene_symbols() -> None:
    record = _parse_mutation(SAMPLE_SSMS["data"]["hits"][0])
    assert record.ssm_id == "07f33888-b319-55fa-a680-a0b924290e55"
    assert record.gene_symbols == ["KRAS"]
    assert record.amino_acid_changes == ["H95Y"]


def _mock_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    return resp


@pytest.mark.asyncio
async def test_search_projects_success() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response(SAMPLE_PROJECTS))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "biosense.infrastructure.external.gdc_client.httpx.AsyncClient",
        return_value=mock_client,
    ):
        client = GdcClient()
        records = await client.search_projects(primary_site="Bronchus and lung")

    assert len(records) == 1
    assert records[0].project_id == "TCGA-LUAD"
    called_params = mock_client.get.await_args.kwargs["params"]
    assert "filters" in called_params


@pytest.mark.asyncio
async def test_search_genes_success() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response(SAMPLE_GENES))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "biosense.infrastructure.external.gdc_client.httpx.AsyncClient",
        return_value=mock_client,
    ):
        client = GdcClient()
        records = await client.search_genes("KRAS")

    assert len(records) == 1
    assert records[0].symbol == "KRAS"


@pytest.mark.asyncio
async def test_search_mutations_success() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response(SAMPLE_SSMS))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "biosense.infrastructure.external.gdc_client.httpx.AsyncClient",
        return_value=mock_client,
    ):
        client = GdcClient()
        records = await client.search_mutations(gene_symbol="KRAS")

    assert len(records) == 1
    assert records[0].gene_symbols == ["KRAS"]


@pytest.mark.asyncio
async def test_search_returns_empty_on_failure() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=ConnectionError("offline"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "biosense.infrastructure.external.gdc_client.httpx.AsyncClient",
        return_value=mock_client,
    ):
        client = GdcClient()
        records = await client.search_projects()

    assert records == []


@pytest.mark.asyncio
async def test_health_check_ok() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response({"status": "OK"}))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "biosense.infrastructure.external.gdc_client.httpx.AsyncClient",
        return_value=mock_client,
    ):
        client = GdcClient()
        assert await client.health_check() is True


@pytest.mark.asyncio
async def test_health_check_failure_returns_false() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=ConnectionError("offline"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "biosense.infrastructure.external.gdc_client.httpx.AsyncClient",
        return_value=mock_client,
    ):
        client = GdcClient()
        assert await client.health_check() is False
