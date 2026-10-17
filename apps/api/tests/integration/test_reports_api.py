import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from biosense.api.dependencies import get_current_user, get_db_session
from biosense.api.main import app

REPO = "biosense.api.v1.reports.SavedReportRepository"


class _FakeSession:
    commit = AsyncMock()


@pytest.fixture(autouse=True)
def _fake_session():
    app.dependency_overrides[get_db_session] = lambda: _FakeSession()
    yield
    app.dependency_overrides.pop(get_db_session, None)


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _row():
    return SimpleNamespace(
        id=uuid.uuid4(),
        created_at=datetime.now(UTC),
        input={"cancer_type": "lung"},
        recommendations=[{"rank": 1}],
    )


@pytest.mark.asyncio
async def test_list_reports_scopes_to_current_user() -> None:
    with patch(f"{REPO}.list_for_user", new_callable=AsyncMock, return_value=[_row()]) as m:
        async with _client() as c:
            response = await c.get("/v1/reports")

    assert response.status_code == 200
    assert response.json()[0]["input"] == {"cancer_type": "lung"}
    m.assert_awaited_once_with("admin")


@pytest.mark.asyncio
async def test_create_report_returns_201_and_saves_for_current_user() -> None:
    with patch(f"{REPO}.create", new_callable=AsyncMock, return_value=_row()) as m:
        async with _client() as c:
            response = await c.post(
                "/v1/reports",
                json={"input": {"cancer_type": "lung"}, "recommendations": [{"rank": 1}]},
            )

    assert response.status_code == 201
    assert m.await_args.args[0] == "admin"


@pytest.mark.asyncio
async def test_create_report_rejects_more_than_50_recommendations() -> None:
    async with _client() as c:
        response = await c.post("/v1/reports", json={"input": {}, "recommendations": [{}] * 51})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_missing_or_foreign_report_returns_404() -> None:
    with patch(f"{REPO}.delete", new_callable=AsyncMock, return_value=False):
        async with _client() as c:
            response = await c.delete(f"/v1/reports/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_report_returns_204() -> None:
    with patch(f"{REPO}.delete", new_callable=AsyncMock, return_value=True):
        async with _client() as c:
            response = await c.delete(f"/v1/reports/{uuid.uuid4()}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_reports_require_authentication() -> None:
    app.dependency_overrides.pop(get_current_user, None)
    async with _client() as c:
        assert (await c.get("/v1/reports")).status_code == 401
        assert (await c.post("/v1/reports", json={})).status_code == 401
        assert (await c.delete(f"/v1/reports/{uuid.uuid4()}")).status_code == 401
