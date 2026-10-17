import pytest
from httpx import ASGITransport, AsyncClient

from biosense.api import dependencies
from biosense.api.dependencies import get_current_user
from biosense.api.main import app
from biosense.config import settings
from biosense.infrastructure.auth.supabase_jwt import SupabaseAuthUser

ADMIN_POSTS = [
    "/v1/graph/sync/schema",
    "/v1/graph/sync/domain",
    "/v1/ingestion/jobs/trigger",
    "/v1/ingestion/literature/harvest",
    "/v1/literature/papers/ingest-text",
]
ADMIN_GETS = ["/v1/ingestion/jobs", "/v1/ingestion/monitoring/status"]
EXPENSIVE_POSTS = [
    "/v1/rnd/design",
    "/v1/recommendations/generate",
    "/v1/literature/rag/query",
    "/v1/literature/rag/evaluate",
]


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(autouse=True)
def _cleanup(monkeypatch):
    monkeypatch.setattr(settings, "admin_emails", "boss@example.com")
    dependencies._request_log.clear()
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ADMIN_POSTS + EXPENSIVE_POSTS)
async def test_post_requires_token(client, path) -> None:
    async with client as c:
        assert (await c.post(path, json={})).status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ADMIN_GETS)
async def test_admin_get_requires_token(client, path) -> None:
    async with client as c:
        assert (await c.get(path)).status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ADMIN_POSTS)
async def test_non_admin_forbidden(client, path) -> None:
    app.dependency_overrides[get_current_user] = lambda: SupabaseAuthUser("u1", "user@example.com")
    async with client as c:
        assert (await c.post(path, json={})).status_code == 403


@pytest.mark.asyncio
async def test_no_admins_configured_fails_closed(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_emails", "")
    app.dependency_overrides[get_current_user] = lambda: SupabaseAuthUser("u1", "boss@example.com")
    async with client as c:
        assert (await c.post("/v1/graph/sync/schema")).status_code == 403


@pytest.mark.asyncio
async def test_public_reads_stay_open(client) -> None:
    async with client as c:
        assert (await c.get("/v1/public-data/regions")).status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_returns_429(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "expensive_rate_limit_per_minute", 2)
    app.dependency_overrides[get_current_user] = lambda: SupabaseAuthUser("u1", "user@example.com")
    async with client as c:
        codes = [(await c.post("/v1/rnd/design", json={})).status_code for _ in range(3)]
    assert codes[:2] != [429, 429]  # first two pass the limiter (422 from validation)
    assert codes[2] == 429
