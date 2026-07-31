import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from biosense.application.services.pipeline_service import PublicDataIngestionPipeline
from biosense.config import settings
from biosense.infrastructure.persistence.postgres.session import async_session_factory

logger = structlog.get_logger()
scheduler = AsyncIOScheduler()


async def scheduled_full_sync() -> None:
    logger.info("scheduled_ingestion_started")
    async with async_session_factory() as session:
        pipeline = PublicDataIngestionPipeline(session)
        try:
            job_id = await pipeline.run_full_sync()
            logger.info("scheduled_ingestion_completed", job_id=str(job_id))
        except Exception as exc:
            logger.error("scheduled_ingestion_failed", error=str(exc))


def start_scheduler() -> None:
    if not settings.ingestion_scheduler_enabled:
        logger.info("ingestion_scheduler_disabled")
        return

    scheduler.add_job(
        scheduled_full_sync,
        trigger=CronTrigger(hour=settings.ingestion_cron_hour, minute=0),
        id="public_data_full_sync",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "ingestion_scheduler_started",
        cron_hour=settings.ingestion_cron_hour,
    )


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("ingestion_scheduler_stopped")
