"""Thin async Neo4j driver wrapper.

A single driver is lazily created and reused (the driver itself pools connections).
`run_write` executes one Cypher statement and returns its records as plain dicts —
the shape every KnowledgeGraphSyncService method needs, and easy to mock in tests
without pulling in the real neo4j driver.
"""

from __future__ import annotations

from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase

from biosense.config import settings

_driver: AsyncDriver | None = None


def get_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )
    return _driver


async def close_driver() -> None:
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


async def run_write(query: str, **params: Any) -> list[dict[str, Any]]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(query, **params)
        return [record.data() async for record in result]
