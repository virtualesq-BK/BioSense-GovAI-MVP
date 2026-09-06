import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from biosense.api.dependencies import get_db_session
from biosense.application.dto.catalog import (
    BiomarkerDetailResponse,
    BiomarkerPriorityScoreResponse,
    BiomarkerSummaryResponse,
    CancerResponse,
    PaperSummaryRefResponse,
    RecognitionMatchResponse,
)
from biosense.application.services.biomarker_priority_service import BiomarkerPriorityService
from biosense.domain.entities.priority_score import BiomarkerPriorityScore
from biosense.domain.services.normalization import normalize_cancer_type
from biosense.infrastructure.persistence.postgres.models import (
    Biomarker,
    BiomarkerRecognitionMatch,
    Cancer,
    CancerBiomarker,
)

router = APIRouter(tags=["Catalog"])


@router.get("/cancers", response_model=list[CancerResponse])
async def list_cancers(session: AsyncSession = Depends(get_db_session)) -> list[CancerResponse]:
    cancers = (await session.execute(select(Cancer))).scalars().all()
    return [
        CancerResponse(
            id=str(c.id), code=c.code, name_en=c.name_en, name_ko=c.name_ko, icd_code=c.icd_code
        )
        for c in cancers
    ]


@router.get("/biomarkers", response_model=list[BiomarkerSummaryResponse])
async def list_biomarkers(
    cancer_type: str | None = Query(default=None),
    include_priority_score: bool = Query(default=False),
    session: AsyncSession = Depends(get_db_session),
) -> list[BiomarkerSummaryResponse]:
    """List biomarkers, optionally filtered by cancer type.

    `include_priority_score=true` additionally computes each biomarker's Biomarker
    Priority Score (requires `cancer_type`) — this calls out to NCI GDC per biomarker,
    so it is opt-in rather than the default for a plain catalog listing.
    """
    query = select(Biomarker).options(
        selectinload(Biomarker.cancers), selectinload(Biomarker.ctdna)
    )

    cancer_code = None
    if cancer_type:
        cancer_code = normalize_cancer_type(cancer_type)
        query = query.join(
            CancerBiomarker, CancerBiomarker.biomarker_id == Biomarker.id
        ).join(Cancer, Cancer.id == CancerBiomarker.cancer_id).where(Cancer.code == cancer_code)

    biomarkers = (await session.execute(query)).scalars().unique().all()

    priority_by_name: dict[str, float] = {}
    if include_priority_score:
        if not cancer_code:
            raise HTTPException(
                status_code=400,
                detail="cancer_type is required when include_priority_score=true",
            )
        service = BiomarkerPriorityService(session)
        scores = await service.score_biomarkers_for_cancer(cancer_code)
        priority_by_name = {s.biomarker_name: s.total_score for s in scores}

    return [
        BiomarkerSummaryResponse(
            id=str(b.id),
            name=b.name,
            gene_symbol=b.gene_symbol,
            ctdna_class=b.ctdna.code if b.ctdna else "",
            cancer_codes=[c.code for c in b.cancers],
            priority_score=priority_by_name.get(b.name),
        )
        for b in biomarkers
    ]


@router.get("/biomarkers/{biomarker_id}", response_model=BiomarkerDetailResponse)
async def get_biomarker(
    biomarker_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> BiomarkerDetailResponse:
    try:
        parsed_id = uuid.UUID(biomarker_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Biomarker not found") from exc

    biomarker = (
        await session.execute(
            select(Biomarker)
            .where(Biomarker.id == parsed_id)
            .options(
                selectinload(Biomarker.cancers),
                selectinload(Biomarker.ctdna),
                selectinload(Biomarker.recognition_matches).selectinload(
                    BiomarkerRecognitionMatch.recognition_strategy
                ),
                selectinload(Biomarker.papers),
            )
        )
    ).scalar_one_or_none()
    if biomarker is None:
        raise HTTPException(status_code=404, detail="Biomarker not found")

    return BiomarkerDetailResponse(
        id=str(biomarker.id),
        name=biomarker.name,
        gene_symbol=biomarker.gene_symbol,
        ctdna_class=biomarker.ctdna.code if biomarker.ctdna else "",
        description=biomarker.description,
        cancer_codes=[c.code for c in biomarker.cancers],
        recognition_matches=[
            RecognitionMatchResponse(
                recognition_code=m.recognition_strategy.code,
                recognition_name=m.recognition_strategy.name,
                match_score=float(m.match_score),
            )
            for m in biomarker.recognition_matches
        ],
        papers=[
            PaperSummaryRefResponse(external_id=p.external_id, title=p.title, source=p.source)
            for p in biomarker.papers
        ],
    )


@router.get(
    "/biomarkers/{biomarker_name}/priority-score",
    response_model=BiomarkerPriorityScoreResponse,
)
async def get_biomarker_priority_score(
    biomarker_name: str,
    cancer_type: str = Query(...),
    session: AsyncSession = Depends(get_db_session),
) -> BiomarkerPriorityScoreResponse:
    service = BiomarkerPriorityService(session)
    score = await service.score_biomarker(biomarker_name, cancer_type)
    if score is None:
        raise HTTPException(
            status_code=404, detail="Biomarker or cancer type not found"
        )
    return _to_priority_response(score)


def _to_priority_response(score: BiomarkerPriorityScore) -> BiomarkerPriorityScoreResponse:
    return BiomarkerPriorityScoreResponse(
        biomarker_name=score.biomarker_name,
        cancer_type=score.cancer_type,
        total_score=score.total_score,
        disease_burden=score.disease_burden,
        molecular_evidence=score.molecular_evidence,
        clinical_evidence=score.clinical_evidence,
        detection_feasibility=score.detection_feasibility,
        sensor_compatibility=score.sensor_compatibility,
        data_confidence=score.data_confidence,
        missing_data_factors=score.missing_data_factors,
    )
