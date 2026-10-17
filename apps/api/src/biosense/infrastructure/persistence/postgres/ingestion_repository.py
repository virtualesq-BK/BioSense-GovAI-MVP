import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.config import settings
from biosense.domain.entities.public_health import (
    PublicDataDocumentRecord,
    TransformedPublicHealthRecord,
)
from biosense.infrastructure.persistence.postgres.models import (
    Cancer,
    IngestionCache,
    IngestionJob,
    PublicDataChunk,
    PublicDataDocument,
    PublicHealthFeature,
)

logger = structlog.get_logger()


class IngestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_job(self, job_type: str, source: str) -> IngestionJob:
        job = IngestionJob(job_type=job_type, status="pending", source=source)
        self._session.add(job)
        await self._session.flush()
        return job

    async def mark_job_running(self, job_id: uuid.UUID) -> None:
        job = await self._session.get(IngestionJob, job_id)
        if job:
            job.status = "running"
            job.started_at = datetime.now(UTC)

    async def complete_job(
        self,
        job_id: uuid.UUID,
        *,
        extracted: int,
        transformed: int,
        embedded: int,
        stored: int,
        metadata: dict | None = None,
    ) -> None:
        job = await self._session.get(IngestionJob, job_id)
        if job:
            job.status = "completed"
            job.records_extracted = extracted
            job.records_transformed = transformed
            job.records_embedded = embedded
            job.records_stored = stored
            job.finished_at = datetime.now(UTC)
            if metadata:
                job.metadata_ = metadata

    async def fail_job(self, job_id: uuid.UUID, error: str) -> None:
        job = await self._session.get(IngestionJob, job_id)
        if job:
            job.status = "failed"
            job.error_message = error
            job.finished_at = datetime.now(UTC)

    async def get_cache(self, cache_key: str) -> dict | None:
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(IngestionCache).where(
                IngestionCache.cache_key == cache_key,
                IngestionCache.expires_at > now,
            )
        )
        row = result.scalar_one_or_none()
        return row.payload if row else None

    async def set_cache(self, cache_key: str, source: str, payload: dict) -> None:
        expires = datetime.now(UTC) + timedelta(hours=settings.ingestion_cache_ttl_hours)
        stmt = insert(IngestionCache).values(
            cache_key=cache_key,
            source=source,
            payload=payload,
            expires_at=expires,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["cache_key"],
            set_={
                "payload": stmt.excluded.payload,
                "source": stmt.excluded.source,
                "expires_at": stmt.excluded.expires_at,
            },
        )
        await self._session.execute(stmt)

    async def purge_expired_cache(self) -> int:
        now = datetime.now(UTC)
        result = await self._session.execute(
            delete(IngestionCache).where(IngestionCache.expires_at <= now)
        )
        return result.rowcount or 0

    async def upsert_public_health_features(
        self, records: list[TransformedPublicHealthRecord]
    ) -> int:
        stored = 0
        for rec in records:
            cancer_id = await self._resolve_cancer_id(rec.cancer_code)
            if cancer_id is None:
                logger.warning("cancer_not_found_skipping", cancer_code=rec.cancer_code)
                continue
            stmt = insert(PublicHealthFeature).values(
                region_code=rec.region_code,
                region_name_ko=rec.region_name_ko,
                cancer_id=cancer_id,
                feature_type=rec.feature_type,
                value=rec.value,
                unit=rec.unit,
                data_year=rec.data_year,
                source=rec.source,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["region_code", "cancer_id", "feature_type", "data_year"],
                set_={
                    "value": stmt.excluded.value,
                    "region_name_ko": stmt.excluded.region_name_ko,
                    "source": stmt.excluded.source,
                    "fetched_at": datetime.now(UTC),
                },
            )
            await self._session.execute(stmt)
            stored += 1
        return stored

    async def upsert_public_data_documents(
        self, documents: list[PublicDataDocumentRecord], embeddings: list[list[float]]
    ) -> int:
        stored = 0
        for doc, embedding in zip(documents, embeddings, strict=True):
            stmt = insert(PublicDataDocument).values(
                external_key=doc.external_key,
                source=doc.source,
                title=doc.title,
                content=doc.content,
                metadata_=doc.metadata,
                data_year=doc.data_year,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["external_key"],
                set_={
                    "title": stmt.excluded.title,
                    "content": stmt.excluded.content,
                    "metadata": stmt.excluded.metadata,
                    "data_year": stmt.excluded.data_year,
                    "updated_at": datetime.now(UTC),
                },
            ).returning(PublicDataDocument.id)
            result = await self._session.execute(stmt)
            document_id = result.scalar_one()

            await self._session.execute(
                delete(PublicDataChunk).where(PublicDataChunk.document_id == document_id)
            )
            chunk = PublicDataChunk(
                document_id=document_id,
                chunk_index=0,
                content=doc.content,
                embedding=embedding,
                metadata_={"source": doc.source, "data_year": doc.data_year},
            )
            self._session.add(chunk)
            stored += 1
        return stored

    async def list_recent_jobs(self, limit: int = 20) -> list[IngestionJob]:
        result = await self._session.execute(
            select(IngestionJob).order_by(IngestionJob.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_job(self, job_id: uuid.UUID) -> IngestionJob | None:
        return await self._session.get(IngestionJob, job_id)

    async def get_monitoring_stats(self) -> dict:
        jobs = await self.list_recent_jobs(limit=50)
        completed = [j for j in jobs if j.status == "completed"]
        failed = [j for j in jobs if j.status == "failed"]
        last_success = max(
            (j.finished_at for j in completed if j.finished_at),
            default=None,
        )
        return {
            "total_jobs": len(jobs),
            "completed_jobs": len(completed),
            "failed_jobs": len(failed),
            "last_success_at": last_success.isoformat() if last_success else None,
            "last_job_status": jobs[0].status if jobs else None,
        }

    async def _resolve_cancer_id(self, cancer_code: str) -> uuid.UUID | None:
        result = await self._session.execute(select(Cancer.id).where(Cancer.code == cancer_code))
        return result.scalar_one_or_none()

    async def cache_raw_records(self, cache_key: str, source: str, records: list[dict]) -> None:
        await self.set_cache(cache_key, source, {"records": records})

    async def load_cached_raw_records(self, cache_key: str) -> list[dict] | None:
        cached = await self.get_cache(cache_key)
        if not cached:
            return None
        return cached.get("records", [])
