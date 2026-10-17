from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.api.dependencies import get_db_session, rate_limit_expensive
from biosense.application.dto.recommendation import (
    ExpectedMetricsResponse,
    GenerateRecommendationRequest,
    GenerateRecommendationResponse,
    SensorRecommendationResponse,
)
from biosense.application.services.recommendation_engine_service import RecommendationEngineService
from biosense.domain.entities.recommendation import RecommendationInput

router = APIRouter(tags=["Recommendations"])


@router.post(
    "/recommendations/generate",
    response_model=GenerateRecommendationResponse,
    dependencies=[Depends(rate_limit_expensive)],
)
async def generate_recommendations(
    body: GenerateRecommendationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> GenerateRecommendationResponse:
    engine = RecommendationEngineService(session)
    inp = RecommendationInput(
        cancer_type=body.cancer_type,
        ctdna_class=body.ctdna_class,
        region_code=body.region_code,
        patient_age=body.patient_age,
        biomarker_name=body.biomarker_name,
        notes=body.notes,
    )
    recs = await engine.generate(inp, top_k=body.top_k)
    return GenerateRecommendationResponse(
        recommendations=[_to_response(r) for r in recs],
        count=len(recs),
    )


def _to_response(rec) -> SensorRecommendationResponse:
    m = rec.expected_metrics
    return SensorRecommendationResponse(
        rank=rec.rank,
        sensor_type=rec.sensor_type,
        sensor_name=rec.sensor_name,
        recognition_strategy=rec.recognition_strategy,
        recognition_name=rec.recognition_name,
        biomarker_name=rec.biomarker_name,
        expected_metrics=ExpectedMetricsResponse(
            sensitivity=m.sensitivity,
            specificity=m.specificity,
            lod_value=m.lod_value,
            lod_unit=m.lod_unit,
            estimated_cost_usd=m.estimated_cost_usd,
        ),
        experimental_protocol=rec.experimental_protocol,
        confidence_score=rec.confidence_score,
        composite_score=rec.composite_score,
        rationale=rec.rationale,
        evidence=rec.evidence,
    )
