import pytest
from httpx import ASGITransport, AsyncClient

from biosense.api.main import app


@pytest.mark.asyncio
async def test_health_returns_response() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "0.1.0"
    assert body["status"] in ("ok", "degraded", "down")
    assert "postgres" in body["dependencies"]
    assert "neo4j" in body["dependencies"]
