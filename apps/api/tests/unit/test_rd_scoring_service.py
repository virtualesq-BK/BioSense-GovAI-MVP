import pytest

from biosense.application.services.rd_scoring_service import RdScoringService
from biosense.domain.entities.biomarker_dimension import EvidenceRef
from biosense.domain.entities.molecular_characterization import (
    Detectability,
    MolecularCharacterizationResult,
)
from biosense.domain.entities.molecular_recognition import (
    RecognitionRecommendation,
    RecognitionStrategyType,
)
from biosense.domain.entities.priority_score import BiomarkerPriorityScore, ScoreComponent
from biosense.domain.entities.sensor_transduction import SensorPlatformType, SensorTransductionCandidate


def _component(score=60.0, missing=False):
    return ScoreComponent(score=score, evidence="e", source="s", confidence=0.5, missing_data=missing)


def _priority_score():
    return BiomarkerPriorityScore(
        biomarker_name="KRAS G12D mutation",
        cancer_type="lung",
        total_score=66.4,
        disease_burden=_component(),
        molecular_evidence=_component(),
        clinical_evidence=_component(70.0),
        detection_feasibility=_component(),
        sensor_compatibility=_component(),
        data_confidence=_component(55.0),
    )


def _characterization():
    return MolecularCharacterizationResult(
        biomarker="KRAS G12D mutation",
        dimension="mutation",
        molecular_characteristics=["char 1"],
        detectability=Detectability(True, 141, "basis", False),
        specificity_features=[],
        limitations=[],
        evidence=[EvidenceRef(source="PubMed", external_id="pmid:1", title="A paper")],
    )


def test_score_combines_all_factors_with_transparent_basis():
    recognition = RecognitionRecommendation(
        strategy=RecognitionStrategyType.DNA_HYBRIDIZATION,
        status="scored",
        compatibility_score=80.0,
        rationale="r",
        confidence=0.7,
    )
    sensor = SensorTransductionCandidate(
        platform=SensorPlatformType.ELECTROCHEMICAL,
        status="scored",
        sensor_name="EC sensor",
        feasibility_score=75.0,
        rationale="r",
    )

    result = RdScoringService().score(
        biomarker_name="KRAS G12D mutation",
        characterization=_characterization(),
        recognition=recognition,
        sensor=sensor,
        priority_score=_priority_score(),
    )

    assert 0.0 <= result.total_score <= 100.0
    assert result.recognition_feasibility.score == 80.0
    assert result.sensor_feasibility.score == 75.0
    assert result.clinical_relevance.score == 70.0
    assert result.data_confidence.score == 55.0
    assert sum(result.weights.values()) == pytest.approx(1.0)
    for factor in result.components.values():
        assert factor.basis  # every score shows its computation basis


def test_score_marks_missing_data_when_no_priority_score_or_recognition():
    result = RdScoringService().score(
        biomarker_name="X",
        characterization=_characterization(),
        recognition=None,
        sensor=None,
        priority_score=None,
    )

    assert result.recognition_feasibility.missing_data is True
    assert result.sensor_feasibility.missing_data is True
    assert result.clinical_relevance.missing_data is True
    assert result.data_confidence.missing_data is True
    assert "Insufficient evidence" in result.recognition_feasibility.basis
