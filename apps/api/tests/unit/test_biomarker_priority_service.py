import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from biosense.application.services.biomarker_priority_service import BiomarkerPriorityService


class FakeCancer:
    def __init__(self, code: str) -> None:
        self.id = uuid.uuid4()
        self.code = code


class FakeMatch:
    def __init__(self, recognition_strategy_id, match_score: float) -> None:
        self.recognition_strategy_id = recognition_strategy_id
        self.match_score = match_score


class FakePaper:
    pass


class FakeBiomarker:
    def __init__(
        self,
        name: str,
        gene_symbol: str | None,
        recognition_matches: list | None = None,
        papers: list | None = None,
    ) -> None:
        self.id = uuid.uuid4()
        self.name = name
        self.gene_symbol = gene_symbol
        self.recognition_matches = recognition_matches or []
        self.papers = papers or []


def _make_service(
    *,
    cancer: FakeCancer | None,
    biomarker: FakeBiomarker | None,
    avg_incidence: float | None,
    mutation_count: int | None,
    sensor_efficiencies: list[float],
) -> tuple[BiomarkerPriorityService, AsyncMock]:
    session = MagicMock()

    async def fake_scalar(query):
        return avg_incidence

    cancer_result = MagicMock()
    cancer_result.scalar_one_or_none = MagicMock(return_value=cancer)

    biomarker_result = MagicMock()
    biomarker_scalars = MagicMock()
    biomarker_scalars.unique.return_value.one_or_none = MagicMock(return_value=biomarker)
    biomarker_result.scalars = MagicMock(return_value=biomarker_scalars)

    efficiency_result = MagicMock()
    efficiency_result.all = MagicMock(return_value=[(e,) for e in sensor_efficiencies])

    async def fake_execute(query):
        query_str = str(query)
        if "cancers" in query_str.lower() and "SELECT cancers" in str(query):
            return cancer_result
        if "biomarkers" in query_str.lower() and "recognition_sensor_uses" not in query_str.lower():
            return biomarker_result
        return efficiency_result

    session.scalar = AsyncMock(side_effect=fake_scalar)
    session.execute = AsyncMock(side_effect=fake_execute)

    gdc = AsyncMock()
    gdc.count_mutations_for_gene = AsyncMock(return_value=mutation_count)

    service = BiomarkerPriorityService(session, gdc=gdc)
    return service, session


@pytest.mark.asyncio
async def test_score_biomarker_returns_none_for_unknown_cancer() -> None:
    service, _ = _make_service(
        cancer=None, biomarker=None, avg_incidence=None, mutation_count=None, sensor_efficiencies=[]
    )
    result = await service.score_biomarker("KRAS G12D mutation", "unknown-cancer-xyz")
    assert result is None


@pytest.mark.asyncio
async def test_score_biomarker_full_evidence() -> None:
    cancer = FakeCancer("lung")
    rec_id = uuid.uuid4()
    biomarker = FakeBiomarker(
        "KRAS G12D mutation",
        "KRAS",
        recognition_matches=[FakeMatch(rec_id, 0.9)],
        papers=[FakePaper(), FakePaper()],
    )
    service, _ = _make_service(
        cancer=cancer,
        biomarker=biomarker,
        avg_incidence=45.0,
        mutation_count=141,
        sensor_efficiencies=[0.85],
    )

    result = await service.score_biomarker("KRAS G12D mutation", "lung")

    assert result is not None
    assert result.biomarker_name == "KRAS G12D mutation"
    assert result.cancer_type == "lung"
    assert result.missing_data_factors == []
    assert result.disease_burden.score == 45.0
    assert result.molecular_evidence.missing_data is False
    assert result.detection_feasibility.score == 90.0
    assert result.sensor_compatibility.score == 85.0
    assert result.data_confidence.score == 100.0
    assert 0 < result.total_score <= 100


@pytest.mark.asyncio
async def test_score_biomarker_missing_evidence_flagged_honestly() -> None:
    cancer = FakeCancer("lung")
    biomarker = FakeBiomarker("Unstudied biomarker", None, recognition_matches=[], papers=[])
    service, _ = _make_service(
        cancer=cancer,
        biomarker=biomarker,
        avg_incidence=None,
        mutation_count=None,
        sensor_efficiencies=[],
    )

    result = await service.score_biomarker("Unstudied biomarker", "lung")

    assert result is not None
    assert set(result.missing_data_factors) == {
        "disease_burden",
        "molecular_evidence",
        "clinical_evidence",
        "detection_feasibility",
        "sensor_compatibility",
    }
    assert result.total_score == 0.0
    assert result.data_confidence.score == 0.0
