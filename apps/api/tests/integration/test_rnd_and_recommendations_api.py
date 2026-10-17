from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from biosense.api import dependencies
from biosense.api.main import app
from biosense.domain.entities.recommendation import ExpectedMetrics, SensorRecommendation

RND_BODY = {"cancer": "lung", "goal": "early detection"}
REC_BODY = {
    "cancer_type": "lung",
    "ctdna_class": "mutation",
    "region_code": "KR-11",
    "patient_age": 60,
}


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    dependencies._request_log.clear()


def _client(raise_app_exceptions: bool = True) -> AsyncClient:
    transport = ASGITransport(app=app, raise_app_exceptions=raise_app_exceptions)
    return AsyncClient(transport=transport, base_url="http://test")


def _recommendation() -> SensorRecommendation:
    return SensorRecommendation(
        rank=1,
        sensor_type="AI_NGS",
        sensor_name="AI-NGS liquid biopsy analyzer",
        recognition_strategy="dna_hybridization",
        recognition_name="DNA hybridization probe",
        biomarker_name="KRAS G12D mutation",
        expected_metrics=ExpectedMetrics(
            sensitivity=0.94,
            specificity=0.96,
            lod_value=0.001,
            lod_unit="ng/mL",
            estimated_cost_usd=450.0,
        ),
        experimental_protocol={},
        confidence_score=0.8,
        composite_score=0.9,
        rationale="r",
        evidence={},
    )


@pytest.mark.asyncio
async def test_recommendations_generate_success() -> None:
    with patch(
        "biosense.api.v1.recommendations.RecommendationEngineService.generate",
        new_callable=AsyncMock,
        return_value=[_recommendation()],
    ):
        async with _client() as c:
            response = await c.post("/v1/recommendations/generate", json=REC_BODY)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["recommendations"][0]["sensor_type"] == "AI_NGS"


@pytest.mark.asyncio
async def test_recommendations_generate_rejects_invalid_age() -> None:
    async with _client() as c:
        response = await c.post(
            "/v1/recommendations/generate", json={**REC_BODY, "patient_age": 200}
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_recommendations_generate_service_failure_returns_json_500() -> None:
    with patch(
        "biosense.api.v1.recommendations.RecommendationEngineService.generate",
        new_callable=AsyncMock,
        side_effect=RuntimeError("neo4j exploded: bolt://secret-host"),
    ):
        async with _client(raise_app_exceptions=False) as c:
            response = await c.post("/v1/recommendations/generate", json=REC_BODY)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


@pytest.mark.asyncio
async def test_rnd_design_requires_cancer_and_goal() -> None:
    async with _client() as c:
        response = await c.post("/v1/rnd/design", json={"cancer": "lung"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_rnd_design_service_failure_returns_json_500() -> None:
    with patch(
        "biosense.api.v1.rnd.RndDesignReportService.generate",
        new_callable=AsyncMock,
        side_effect=RuntimeError("GDC timeout"),
    ):
        async with _client(raise_app_exceptions=False) as c:
            response = await c.post("/v1/rnd/design", json=RND_BODY)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


@pytest.mark.asyncio
async def test_500_response_keeps_cors_header_for_allowed_origin() -> None:
    with patch(
        "biosense.api.v1.rnd.RndDesignReportService.generate",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    ):
        async with _client(raise_app_exceptions=False) as c:
            response = await c.post(
                "/v1/rnd/design", json=RND_BODY, headers={"Origin": "http://localhost:3000"}
            )

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
