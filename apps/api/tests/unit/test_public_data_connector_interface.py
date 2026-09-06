"""Verify every external client implements the common PublicDataConnector surface."""

from unittest.mock import AsyncMock, patch

import pytest

from biosense.infrastructure.external.base import PublicDataConnector
from biosense.infrastructure.external.europe_pmc_client import EuropePmcClient
from biosense.infrastructure.external.gdc_client import GdcClient
from biosense.infrastructure.external.korean_health_clients import KdcaClient, KosisClient
from biosense.infrastructure.external.pubmed_client import PubmedClient

ALL_CONNECTOR_CLASSES = [KosisClient, KdcaClient, PubmedClient, GdcClient, EuropePmcClient]


@pytest.mark.parametrize("connector_cls", ALL_CONNECTOR_CLASSES)
def test_client_implements_interface(connector_cls: type) -> None:
    instance = connector_cls()
    assert isinstance(instance, PublicDataConnector)
    assert isinstance(instance.SOURCE, str) and instance.SOURCE


@pytest.mark.asyncio
async def test_kosis_search_delegates_to_fetch_cancer_statistics() -> None:
    client = KosisClient()
    with patch.object(
        client, "fetch_cancer_statistics", new_callable=AsyncMock, return_value=[]
    ) as mocked:
        await client.search("ignored query", filters={"year": 2020})
    mocked.assert_awaited_once_with(year=2020)


@pytest.mark.asyncio
async def test_kdca_fetch_by_year_identifier() -> None:
    client = KdcaClient()
    with patch.object(
        client, "fetch_cancer_statistics", new_callable=AsyncMock, return_value=[]
    ) as mocked:
        await client.fetch("2021")
    mocked.assert_awaited_once_with(year=2021)


@pytest.mark.asyncio
async def test_kdca_fetch_invalid_identifier_returns_none() -> None:
    client = KdcaClient()
    result = await client.fetch("not-a-year")
    assert result is None


@pytest.mark.asyncio
async def test_pubmed_search_delegates_with_max_results() -> None:
    client = PubmedClient()
    with patch.object(
        client, "search_and_fetch", new_callable=AsyncMock, return_value=[]
    ) as mocked:
        await client.search("ctDNA", filters={"max_results": 5})
    mocked.assert_awaited_once_with("ctDNA", max_results=5)


@pytest.mark.asyncio
async def test_gdc_search_dispatches_by_entity() -> None:
    client = GdcClient()
    with patch.object(
        client, "search_genes", new_callable=AsyncMock, return_value=[]
    ) as mocked_genes:
        await client.search("KRAS", filters={"entity": "genes"})
    mocked_genes.assert_awaited_once_with("KRAS")

    with patch.object(
        client, "search_mutations", new_callable=AsyncMock, return_value=[]
    ) as mocked_muts:
        await client.search("KRAS", filters={"entity": "mutations"})
    mocked_muts.assert_awaited_once_with(gene_symbol="KRAS")

    with patch.object(
        client, "search_projects", new_callable=AsyncMock, return_value=[]
    ) as mocked_projects:
        await client.search("Bronchus and lung")
    mocked_projects.assert_awaited_once_with(primary_site="Bronchus and lung")


@pytest.mark.asyncio
async def test_europe_pmc_search_delegates_with_max_results() -> None:
    client = EuropePmcClient()
    with patch.object(
        client, "search_and_fetch", new_callable=AsyncMock, return_value=[]
    ) as mocked:
        await client.search("ctDNA", filters={"max_results": 10})
    mocked.assert_awaited_once_with("ctDNA", max_results=10)
