import asyncio

from biosense.application.dto.health import (
    DependenciesHealth,
    DependencyStatus,
    HealthResponse,
    HealthStatus,
)
from biosense.config import settings


async def _check_postgres() -> DependencyStatus:
    try:
        import asyncpg

        url = settings.async_database_url.replace("postgresql+asyncpg://", "postgresql://")
        conn = await asyncio.wait_for(asyncpg.connect(url), timeout=3.0)
        await conn.close()
        return DependencyStatus.OK
    except Exception:
        return DependencyStatus.DOWN


async def _check_neo4j() -> DependencyStatus:
    try:
        from neo4j import AsyncGraphDatabase

        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        async with driver.session() as session:
            await asyncio.wait_for(session.run("RETURN 1"), timeout=3.0)
        await driver.close()
        return DependencyStatus.OK
    except Exception:
        return DependencyStatus.DOWN


async def get_health() -> HealthResponse:
    postgres, neo4j = await asyncio.gather(_check_postgres(), _check_neo4j())
    deps = DependenciesHealth(postgres=postgres, neo4j=neo4j)

    # Postgres is the primary (required) dependency.
    # Neo4j powers the knowledge-graph feature but is treated as optional:
    # its absence degrades graph-based recommendations but does not take
    # the whole platform offline.
    if postgres == DependencyStatus.OK:
        status = HealthStatus.OK
    else:
        status = HealthStatus.DOWN

    return HealthResponse(status=status, dependencies=deps)
