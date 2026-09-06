"""Harvest PubMed abstracts into the literature RAG store."""

from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.application.services.literature_ingestion_service import LiteratureIngestionPipeline
from biosense.domain.entities.literature import RawPaperRecord
from biosense.infrastructure.external.pubmed_client import DEFAULT_PUBMED_QUERIES, PubmedClient
from biosense.infrastructure.persistence.postgres.literature_repository import LiteratureRepository

logger = structlog.get_logger()


class PubmedHarvestService:
    """Search PubMed → ingest abstracts via LiteratureIngestionPipeline.ingest_text()."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        pubmed: PubmedClient | None = None,
        pipeline: LiteratureIngestionPipeline | None = None,
    ) -> None:
        self._session = session
        self._pubmed = pubmed or PubmedClient()
        self._pipeline = pipeline or LiteratureIngestionPipeline(session)
        self._repo = LiteratureRepository(session)

    async def harvest(
        self,
        *,
        queries: list[str] | None = None,
        max_results_per_query: int = 20,
    ) -> dict:
        terms = queries or list(DEFAULT_PUBMED_QUERIES)
        records = await self._pubmed.harvest_default(
            max_results_per_query=max_results_per_query,
            queries=terms,
        )

        harvested = 0
        skipped = 0
        failed = 0
        paper_ids: list[str] = []

        for record in records:
            try:
                paper_id, status = await self._ingest_record(record)
                if status == "harvested":
                    harvested += 1
                    paper_ids.append(str(paper_id))
                else:
                    skipped += 1
            except Exception as exc:
                failed += 1
                logger.error(
                    "pubmed_ingest_failed",
                    external_id=record.external_id,
                    error=str(exc),
                )

        message = (
            f"PubMed harvest done: harvested={harvested}, skipped={skipped}, "
            f"failed={failed}, queries={len(terms)}"
        )
        logger.info(
            "pubmed_harvest_service_complete",
            harvested=harvested,
            skipped=skipped,
            failed=failed,
        )
        return {
            "harvested": harvested,
            "skipped": skipped,
            "failed": failed,
            "paper_ids": paper_ids,
            "message": message,
        }

    async def _ingest_record(self, record: RawPaperRecord) -> tuple[object, str]:
        if not record.abstract.strip():
            return None, "skipped"

        existing = await self._repo.get_paper_by_external_id(record.external_id)
        if existing and existing.ingestion_status == "indexed" and existing.chunk_count > 0:
            return existing.id, "skipped"

        paper_id = await self._pipeline.ingest_text(
            external_id=record.external_id,
            title=record.title,
            text=record.abstract,
            authors=record.authors or None,
            source="pubmed",
            abstract=record.abstract,
            published_at=record.published_at,
            metadata={
                "journal": record.journal,
                "doi": record.doi,
                "source": "pubmed",
            },
        )
        return paper_id, "harvested"
