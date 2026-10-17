import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from biosense.application.services.pipeline_service import PublicDataIngestionPipeline
from biosense.application.services.pubmed_harvest_service import PubmedHarvestService
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


async def scheduled_literature_harvest() -> None:
    """Weekly PubMed harvest: search DEFAULT_PUBMED_QUERIES → ingest abstracts into RAG."""
    logger.info("scheduled_literature_harvest_started")
    async with async_session_factory() as session:
        service = PubmedHarvestService(session)
        try:
            result = await service.harvest(
                max_results_per_query=settings.literature_harvest_max_results_per_query,
            )
            logger.info(
                "scheduled_literature_harvest_completed",
                harvested=result["harvested"],
                skipped=result["skipped"],
                failed=result["failed"],
            )
        except Exception as exc:
            logger.error("scheduled_literature_harvest_failed", error=str(exc))


def start_scheduler() -> None:
    any_registered = False

    if settings.ingestion_scheduler_enabled:
        scheduler.add_job(
            scheduled_full_sync,
            trigger=CronTrigger(hour=settings.ingestion_cron_hour, minute=0),
            id="public_data_full_sync",
            replace_existing=True,
        )
        logger.info("public_data_sync_job_registered", cron_hour=settings.ingestion_cron_hour)
        any_registered = True
    else:
        logger.info("ingestion_scheduler_disabled")

    if settings.literature_harvest_scheduler_enabled:
        scheduler.add_job(
            scheduled_literature_harvest,
            trigger=CronTrigger(
                day_of_week=settings.literature_harvest_cron_day_of_week,
                hour=settings.literature_harvest_cron_hour,
                minute=0,
            ),
            id="literature_harvest",
            replace_existing=True,
        )
        logger.info(
            "literature_harvest_job_registered",
            day_of_week=settings.literature_harvest_cron_day_of_week,
            cron_hour=settings.literature_harvest_cron_hour,
        )
        any_registered = True
    else:
        logger.info("literature_harvest_scheduler_disabled")

    if any_registered:
        scheduler.start()
        logger.info("scheduler_started")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("ingestion_scheduler_stopped")
