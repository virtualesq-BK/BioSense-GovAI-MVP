from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from biosense.api.main import app


@pytest.mark.asyncio
async def test_harvest_literature_endpoint() -> None:
    paper_id = uuid4()
    with patch(
        "biosense.api.v1.ingestion.PubmedHarvestService.harvest",
        new_callable=AsyncMock,
        return_value={
            "harvested": 1,
            "skipped": 0,
            "failed": 0,
            "paper_ids": [str(paper_id)],
            "message": "PubMed harvest done: harvested=1, skipped=0, failed=0, queries=1",
        },
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/ingestion/literature/harvest",
                json={"queries": ["ctDNA biosensor"], "max_results_per_query": 5},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["harvested"] == 1
    assert body["paper_ids"] == [str(paper_id)]
    assert "PubMed harvest" in body["message"]


@pytest.mark.asyncio
async def test_harvest_literature_endpoint_defaults() -> None:
    with patch(
        "biosense.api.v1.ingestion.PubmedHarvestService.harvest",
        new_callable=AsyncMock,
        return_value={
            "harvested": 0,
            "skipped": 0,
            "failed": 0,
            "paper_ids": [],
            "message": "PubMed harvest done: harvested=0, skipped=0, failed=0, queries=4",
        },
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/v1/ingestion/literature/harvest", json={})

    assert response.status_code == 200
    assert response.json()["harvested"] == 0
