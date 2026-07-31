import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.application.services.embed_service import EmbedService
from biosense.application.services.extract_service import ExtractService
from biosense.application.services.store_service import StoreService
from biosense.application.services.transform_service import TransformService
from biosense.infrastructure.persistence.postgres.ingestion_repository import IngestionRepository

logger = structlog.get_logger()


class PublicDataIngestionPipeline:
    """ETL pipeline: Extract → Transform → Embed → Store."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = IngestionRepository(session)
        self._extract = ExtractService(self._repo)
        self._transform = TransformService()
        self._embed = EmbedService()
        self._store = StoreService(self._repo)
        self._session = session

    async def run_kosis(self, year: int = 2023) -> uuid.UUID:
        return await self._run("kosis_cancer", "KOSIS", year, self._extract.extract_kosis)

    async def run_kdca(self, year: int = 2023) -> uuid.UUID:
        return await self._run("kdca_cancer", "KDCA", year, self._extract.extract_kdca)

    async def run_full_sync(self, year: int = 2023) -> uuid.UUID:
        job = await self._repo.create_job("full_sync", "KOSIS+KDCA")
        await self._session.commit()
        try:
            await self._repo.mark_job_running(job.id)
            await self._session.commit()

            raw = await self._extract.extract_kosis(year)
            raw += await self._extract.extract_kdca(year)
            features, documents = self._transform.transform_records(raw)
            embeddings = await self._embed.embed_documents(documents)
            stored_features = await self._store.store_health_features(features)
            stored_docs = await self._store.store_documents(documents, embeddings)
            await self._store.purge_expired_cache()

            await self._repo.complete_job(
                job.id,
                extracted=len(raw),
                transformed=len(features),
                embedded=len(embeddings),
                stored=stored_features + stored_docs,
                metadata={"year": year},
            )
            await self._session.commit()
            return job.id
        except Exception as exc:
            await self._repo.fail_job(job.id, str(exc))
            await self._session.commit()
            raise

    async def _run(self, job_type: str, source: str, year: int, extract_fn) -> uuid.UUID:
        job = await self._repo.create_job(job_type, source)
        await self._session.commit()
        try:
            await self._repo.mark_job_running(job.id)
            await self._session.commit()

            raw = await extract_fn(year)
            features, documents = self._transform.transform_records(raw)
            embeddings = await self._embed.embed_documents(documents)
            stored_features = await self._store.store_health_features(features)
            stored_docs = await self._store.store_documents(documents, embeddings)
            await self._store.purge_expired_cache()

            await self._repo.complete_job(
                job.id,
                extracted=len(raw),
                transformed=len(features),
                embedded=len(embeddings),
                stored=stored_features + stored_docs,
                metadata={"year": year},
            )
            await self._session.commit()
            logger.info("pipeline_complete", job_id=str(job.id), source=source)
            return job.id
        except Exception as exc:
            await self._repo.fail_job(job.id, str(exc))
            await self._session.commit()
            logger.error("pipeline_failed", job_id=str(job.id), error=str(exc))
            raise
