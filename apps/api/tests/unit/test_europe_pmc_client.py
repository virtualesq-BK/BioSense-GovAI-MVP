from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from biosense.infrastructure.external.europe_pmc_client import (
    EuropePmcClient,
    _parse_result,
)

SAMPLE_RESULT = {
    "id": "42024570",
    "pmid": "42024570",
    "doi": "10.1021/acs.analchem.6c00173",
    "title": "A Disposable CRISPR-Nanozyme Electrochemical Biosensor for ctDNA.",
    "authorString": "Liu X, Shi F, Hou C.",
    "journalInfo": {"journal": {"title": "Analytical chemistry"}},
    "pubYear": "2026",
    "firstPublicationDate": "2026-04-23",
    "abstractText": "We report an electrochemical biosensor for ctDNA detection.",
    "isOpenAccess": "N",
}

SAMPLE_SEARCH_RESPONSE = {"resultList": {"result": [SAMPLE_RESULT]}}


def test_parse_result() -> None:
    record = _parse_result(SAMPLE_RESULT)
    assert record is not None
    assert record.external_id == "pmid:42024570"
    assert "CRISPR" in record.title
    assert record.journal == "Analytical chemistry"
    assert record.doi == "10.1021/acs.analchem.6c00173"
    assert record.published_at == date(2026, 4, 23)
    assert record.authors == ["Liu X", "Shi F", "Hou C"]


def test_parse_result_falls_back_to_epmc_id_without_pmid() -> None:
    row = dict(SAMPLE_RESULT)
    row.pop("pmid")
    row["id"] = "PPR12345"
    record = _parse_result(row)
    assert record is not None
    assert record.external_id == "epmc:PPR12345"


def test_parse_result_returns_none_without_title() -> None:
    row = dict(SAMPLE_RESULT)
    row["title"] = ""
    assert _parse_result(row) is None


def _mock_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    return resp


@pytest.mark.asyncio
async def test_search_and_fetch_success() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response(SAMPLE_SEARCH_RESPONSE))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "biosense.infrastructure.external.europe_pmc_client.httpx.AsyncClient",
            return_value=mock_client,
        ),
        patch(
            "biosense.infrastructure.external.europe_pmc_client.asyncio.sleep",
            new_callable=AsyncMock,
        ),
    ):
        client = EuropePmcClient()
        records = await client.search_and_fetch("ctDNA biosensor", max_results=5)

    assert len(records) == 1
    assert records[0].external_id == "pmid:42024570"


@pytest.mark.asyncio
async def test_search_and_fetch_returns_empty_on_failure() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=ConnectionError("offline"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "biosense.infrastructure.external.europe_pmc_client.httpx.AsyncClient",
            return_value=mock_client,
        ),
        patch(
            "biosense.infrastructure.external.europe_pmc_client.asyncio.sleep",
            new_callable=AsyncMock,
        ),
    ):
        client = EuropePmcClient()
        records = await client.search_and_fetch("ctDNA", max_results=5)

    assert records == []


@pytest.mark.asyncio
async def test_health_check_ok() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        return_value=_mock_response({"resultList": {"result": []}})
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "biosense.infrastructure.external.europe_pmc_client.httpx.AsyncClient",
        return_value=mock_client,
    ):
        client = EuropePmcClient()
        assert await client.health_check() is True


@pytest.mark.asyncio
async def test_health_check_failure_returns_false() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=ConnectionError("offline"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "biosense.infrastructure.external.europe_pmc_client.httpx.AsyncClient",
        return_value=mock_client,
    ):
        client = EuropePmcClient()
        assert await client.health_check() is False
