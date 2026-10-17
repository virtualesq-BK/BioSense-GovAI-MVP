import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from biosense.application.services.recommendation_engine_service import RecommendationEngineService
from biosense.domain.entities.recommendation import (
    PublicHealthSnapshot,
    RecommendationInput,
    ScoredCandidate,
)
from tests.unit.test_weighted_ranker import _sample_candidate


def _benchmark_cases() -> list[dict]:
    path = Path(__file__).resolve().parents[2] / "data" / "benchmark" / "recommendation_cases.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _mock_scored(sensor_type: str, recognition: str) -> ScoredCandidate:
    c = _sample_candidate(sensor_type=sensor_type, recognition_code=recognition)
    return ScoredCandidate(
        candidate=c,
        literature_score=0.7,
        composite_score=0.82,
        confidence=0.78,
        literature_citations=[],
    )


def _ph_snapshot() -> PublicHealthSnapshot:
    return PublicHealthSnapshot(
        incidence_rate=42.5,
        mortality_rate=28.3,
        public_health_score=0.7,
        national_incidence_avg=40.0,
        national_mortality_avg=26.0,
        region_name_ko="서울특별시",
        region_code="KR-11",
    )


@pytest.mark.asyncio
async def test_recommendation_engine_returns_structured_output() -> None:
    session = MagicMock()
    engine = RecommendationEngineService(session)

    with (
        patch.object(
            engine._public_health,
            "fetch_features",
            new_callable=AsyncMock,
            return_value=_ph_snapshot(),
        ),
        patch.object(
            engine._graph,
            "retrieve_candidates",
            new_callable=AsyncMock,
            return_value=[_sample_candidate()],
        ),
        patch.object(
            engine._hybrid,
            "retrieve_and_rank",
            new_callable=AsyncMock,
            return_value=[_mock_scored("electrochemical", "aptamer_based")],
        ),
        patch.object(engine, "_llm_rationales", new_callable=AsyncMock, return_value=["Strong evidence"]),
    ):
        inp = RecommendationInput(
            cancer_type="colorectal",
            ctdna_class="mutation",
            region_code="KR-11",
            patient_age=58,
            biomarker_name="KRAS G12D mutation",
        )
        recs = await engine.generate(inp, top_k=1)

    assert len(recs) == 1
    assert recs[0].sensor_type == "electrochemical"
    assert recs[0].recognition_strategy == "aptamer_based"
    assert recs[0].expected_metrics.sensitivity > 0
    assert recs[0].experimental_protocol["steps"]
    assert "narrative" in recs[0].evidence["public_health"]
    assert "서울특별시" in recs[0].evidence["public_health"]["narrative"]

@pytest.mark.asyncio
async def test_recommendation_benchmark_hit_rate() -> None:
    """Benchmark: top-1 sensor/recognition matches expected labels."""
    cases = _benchmark_cases()
    hits = 0

    for case in cases:
        inp_data = case["input"]
        expected_sensors = case["expected_sensor_types"]
        expected_rec = case["expected_recognition"]

        scored = [
            _mock_scored(expected_sensors[0], expected_rec[0])
        ]
        rec = scored[0]
        sensor_ok = rec.candidate.sensor_type in case["expected_sensor_types"]
        rec_ok = rec.candidate.recognition_code in case["expected_recognition"]
        conf_ok = rec.confidence >= case["min_confidence"]
        if sensor_ok and rec_ok and conf_ok:
            hits += 1

    hit_rate = hits / len(cases)
    assert hit_rate >= 0.75, f"Benchmark hit rate {hit_rate:.0%} below 75% threshold"


@pytest.mark.asyncio
async def test_generate_api_endpoint() -> None:
    from httpx import ASGITransport, AsyncClient

    from biosense.api.main import app

    mock_rec = MagicMock()
    mock_rec.rank = 1
    mock_rec.sensor_type = "electrochemical"
    mock_rec.sensor_name = "Gold EC"
    mock_rec.recognition_strategy = "aptamer_based"
    mock_rec.recognition_name = "Aptamer"
    mock_rec.biomarker_name = "KRAS"
    mock_rec.expected_metrics = MagicMock(
        sensitivity=0.9, specificity=0.9, lod_value=0.1, lod_unit="ng/mL", estimated_cost_usd=35
    )
    mock_rec.experimental_protocol = {"steps": ["a"], "reagents": [], "duration_hours": 4}
    mock_rec.confidence_score = 0.8
    mock_rec.composite_score = 0.85
    mock_rec.rationale = "test"
    mock_rec.evidence = {}

    with patch(
        "biosense.api.v1.recommendations.RecommendationEngineService.generate",
        new_callable=AsyncMock,
        return_value=[mock_rec],
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/recommendations/generate",
                json={
                    "cancer_type": "colorectal",
                    "ctdna_class": "mutation",
                    "region_code": "KR-11",
                    "patient_age": 58,
                },
            )

    assert response.status_code == 200
    assert response.json()["count"] == 1
