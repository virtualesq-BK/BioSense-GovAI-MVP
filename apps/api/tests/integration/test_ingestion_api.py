from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from biosense.api.main import app


@pytest.mark.asyncio
async def test_list_regions() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/public-data/regions")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 17
    assert data[0]["code"].startswith("KR-")


@pytest.mark.asyncio
async def test_trigger_ingestion_endpoint() -> None:
    job_id = uuid4()
    with patch(
        "biosense.api.v1.ingestion.PublicDataIngestionPipeline.run_full_sync",
        new_callable=AsyncMock,
        return_value=job_id,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/ingestion/jobs/trigger",
                json={"source": "full", "year": 2023},
            )

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == str(job_id)


@pytest.mark.asyncio
async def test_monitoring_status_endpoint() -> None:
    with patch(
        "biosense.api.v1.ingestion.MonitoringService.get_status",
        new_callable=AsyncMock,
        return_value={
            "total_jobs": 1,
            "completed_jobs": 1,
            "failed_jobs": 0,
            "last_success_at": "2026-07-01T00:00:00+00:00",
            "last_job_status": "completed",
            "recent_jobs": [],
        },
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/v1/ingestion/monitoring/status")

    assert response.status_code == 200
    assert response.json()["completed_jobs"] == 1
