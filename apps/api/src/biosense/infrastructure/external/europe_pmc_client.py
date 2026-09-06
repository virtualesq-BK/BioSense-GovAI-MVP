"""Europe PMC RESTful API client (open-access, no authentication required).

Verified live (2026-09-07) against https://www.ebi.ac.uk/europepmc/webservices/rest —
see docs/data-access.md. Complements PubmedClient: PubMed/E-utilities gives abstracts
only, Europe PMC additionally flags open-access full text (`isOpenAccess`).
"""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

import httpx
import structlog

from biosense.config import settings
from biosense.domain.entities.literature import RawPaperRecord
from biosense.infrastructure.common.retry import with_retry
from biosense.infrastructure.external.base import PublicDataConnector

logger = structlog.get_logger()


class EuropePmcClient(PublicDataConnector):
    """Search Europe PMC for literature, normalized to RawPaperRecord."""

    SOURCE = "europepmc"

    def __init__(self) -> None:
        self._base = settings.europe_pmc_base_url.rstrip("/")

    async def search(
        self, query: str, filters: dict[str, Any] | None = None
    ) -> list[RawPaperRecord]:
        max_results = (filters or {}).get("max_results", 20)
        return await self.search_and_fetch(query, max_results=max_results)

    async def fetch(self, identifier: str) -> RawPaperRecord | None:
        """Fetch a single article by PMID (with or without a `pmid:` prefix)."""
        pmid = identifier.removeprefix("pmid:")
        records = await self.search_and_fetch(f"EXT_ID:{pmid} AND SRC:MED", max_results=1)
        return records[0] if records else None

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self._base}/search",
                    params={"query": "cancer", "format": "json", "pageSize": 1},
                )
                response.raise_for_status()
                payload = response.json()
            return "resultList" in payload
        except Exception as exc:
            logger.warning("europepmc_health_check_failed", error=str(exc))
            return False

    async def search_and_fetch(
        self, query: str, *, max_results: int = 20
    ) -> list[RawPaperRecord]:
        async def _call() -> list[RawPaperRecord]:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self._base}/search",
                    params={
                        "query": query,
                        "format": "json",
                        "resultType": "core",
                        "pageSize": max_results,
                    },
                )
                response.raise_for_status()
                payload = response.json()

            results = payload.get("resultList", {}).get("result")
            if not isinstance(results, list):
                raise ValueError("Europe PMC search returned no result list")
            return [_parse_result(r) for r in results if _parse_result(r) is not None]

        try:
            # Conservative throttle: no documented hard limit, community reports ~10 req/s.
            await asyncio.sleep(0.15)
            return await with_retry(_call, operation_name="europepmc_search_fetch")
        except Exception as exc:
            logger.error("europepmc_fetch_failed", query=query, error=str(exc))
            return []


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_result(row: dict) -> RawPaperRecord | None:
    title = (row.get("title") or "").strip()
    if not title:
        return None

    pmid = row.get("pmid")
    external_id = f"pmid:{pmid}" if pmid else f"epmc:{row.get('id', '')}"

    author_string = row.get("authorString") or ""
    authors = [a.strip().rstrip(".") for a in author_string.split(",") if a.strip()]

    journal = (row.get("journalInfo") or {}).get("journal", {}).get("title")

    published_at = _parse_date(row.get("firstPublicationDate"))
    if published_at is None:
        pub_year = row.get("pubYear")
        if pub_year and str(pub_year).isdigit():
            published_at = date(int(pub_year), 1, 1)

    return RawPaperRecord(
        external_id=external_id,
        title=title,
        abstract=row.get("abstractText") or "",
        journal=journal,
        published_at=published_at,
        doi=row.get("doi"),
        authors=authors,
    )
