import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.infrastructure.persistence.postgres.ingestion_repository import IngestionRepository

logger = structlog.get_logger()


class MonitoringService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = IngestionRepository(session)

    async def get_status(self) -> dict:
        stats = await self._repo.get_monitoring_stats()
        jobs = await self._repo.list_recent_jobs(limit=10)
        stats["recent_jobs"] = [
            {
                "id": str(j.id),
                "job_type": j.job_type,
                "status": j.status,
                "source": j.source,
                "records_stored": j.records_stored,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
                "error_message": j.error_message,
            }
            for j in jobs
        ]
        logger.info("monitoring_status_fetched", total_jobs=stats["total_jobs"])
        return stats
