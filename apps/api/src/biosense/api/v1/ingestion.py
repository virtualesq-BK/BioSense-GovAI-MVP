import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.api.dependencies import get_db_session, require_admin
from biosense.application.dto.ingestion import (
    CancerStatsResponse,
    HarvestLiteratureRequest,
    HarvestLiteratureResponse,
    IngestionJobResponse,
    MonitoringStatusResponse,
    RegionResponse,
    TriggerIngestionRequest,
    TriggerIngestionResponse,
)
from biosense.application.services.monitoring_service import MonitoringService
from biosense.application.services.pipeline_service import PublicDataIngestionPipeline
from biosense.application.services.pubmed_harvest_service import PubmedHarvestService
from biosense.infrastructure.external.seed_loader import KR_REGIONS
from biosense.infrastructure.persistence.postgres.ingestion_repository import IngestionRepository
from biosense.infrastructure.persistence.postgres.models import Cancer, PublicHealthFeature

router = APIRouter(tags=["Ingestion", "Public Data"])


@router.post(
    "/ingestion/jobs/trigger",
    response_model=TriggerIngestionResponse,
    dependencies=[Depends(require_admin)],
)
async def trigger_ingestion(
    body: TriggerIngestionRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TriggerIngestionResponse:
    pipeline = PublicDataIngestionPipeline(session)
    if body.source == "kosis":
        job_id = await pipeline.run_kosis(year=body.year)
    elif body.source == "kdca":
        job_id = await pipeline.run_kdca(year=body.year)
    else:
        job_id = await pipeline.run_full_sync(year=body.year)
    return TriggerIngestionResponse(
        job_id=str(job_id),
        message=f"Ingestion job completed for source={body.source}",
    )


@router.post(
    "/ingestion/literature/harvest",
    response_model=HarvestLiteratureResponse,
    dependencies=[Depends(require_admin)],
)
async def harvest_literature(
    body: HarvestLiteratureRequest | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> HarvestLiteratureResponse:
    request = body or HarvestLiteratureRequest()
    service = PubmedHarvestService(session)
    result = await service.harvest(
        queries=request.queries,
        max_results_per_query=request.max_results_per_query,
    )
    return HarvestLiteratureResponse(**result)


@router.get(
    "/ingestion/jobs",
    response_model=list[IngestionJobResponse],
    dependencies=[Depends(require_admin)],
)
async def list_ingestion_jobs(
    session: AsyncSession = Depends(get_db_session),
) -> list[IngestionJobResponse]:
    repo = IngestionRepository(session)
    jobs = await repo.list_recent_jobs()
    return [_job_to_response(j) for j in jobs]


@router.get(
    "/ingestion/jobs/{job_id}",
    response_model=IngestionJobResponse,
    dependencies=[Depends(require_admin)],
)
async def get_ingestion_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> IngestionJobResponse:
    repo = IngestionRepository(session)
    job = await repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job)


@router.get(
    "/ingestion/monitoring/status",
    response_model=MonitoringStatusResponse,
    dependencies=[Depends(require_admin)],
)
async def get_monitoring_status(
    session: AsyncSession = Depends(get_db_session),
) -> MonitoringStatusResponse:
    try:
        service = MonitoringService(session)
        data = await service.get_status()
        return MonitoringStatusResponse(**data)
    except Exception:
        # In local/dev, API should remain usable even if DB is temporarily unavailable.
        return MonitoringStatusResponse(
            total_jobs=0,
            completed_jobs=0,
            failed_jobs=0,
            last_success_at=None,
            last_job_status="db_down",
            recent_jobs=[],
        )


@router.get("/public-data/regions", response_model=list[RegionResponse])
async def list_regions() -> list[RegionResponse]:
    return [RegionResponse(**r) for r in KR_REGIONS]


@router.get("/public-data/cancer-stats", response_model=CancerStatsResponse)
async def get_cancer_stats(
    region_code: str,
    cancer_type: str,
    year: int | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> CancerStatsResponse:
    cancer_result = await session.execute(select(Cancer.id).where(Cancer.code == cancer_type))
    cancer_id = cancer_result.scalar_one_or_none()
    if not cancer_id:
        raise HTTPException(status_code=404, detail="Cancer type not found")

    query = select(PublicHealthFeature).where(
        PublicHealthFeature.region_code == region_code,
        PublicHealthFeature.cancer_id == cancer_id,
    )
    if year:
        query = query.where(PublicHealthFeature.data_year == year)

    result = await session.execute(query)
    features = list(result.scalars().all())
    if not features:
        raise HTTPException(status_code=404, detail="Statistics not found")

    incidence = next((f for f in features if f.feature_type == "incidence"), None)
    mortality = next((f for f in features if f.feature_type == "mortality"), None)
    ref = incidence or mortality or features[0]

    return CancerStatsResponse(
        region_code=region_code,
        cancer_type=cancer_type,
        incidence_rate=float(incidence.value) if incidence else None,
        mortality_rate=float(mortality.value) if mortality else None,
        data_year=ref.data_year,
        source=ref.source,
    )


def _job_to_response(job) -> IngestionJobResponse:
    return IngestionJobResponse(
        id=str(job.id),
        job_type=job.job_type,
        status=job.status,
        source=job.source,
        records_extracted=job.records_extracted,
        records_transformed=job.records_transformed,
        records_embedded=job.records_embedded,
        records_stored=job.records_stored,
        error_message=job.error_message,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        created_at=job.created_at.isoformat(),
    )
