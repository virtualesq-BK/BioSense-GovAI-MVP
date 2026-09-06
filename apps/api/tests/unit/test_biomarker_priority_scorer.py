from biosense.domain.entities.priority_score import ScoreComponent
from biosense.domain.services.biomarker_priority_scorer import (
    BiomarkerPriorityScorer,
    count_to_score,
    fraction_to_score,
    rate_to_score,
)


def _component(score: float, missing: bool = False) -> ScoreComponent:
    return ScoreComponent(
        score=score, evidence="test", source="test", confidence=0.5, missing_data=missing
    )


def test_compute_total_score_all_max() -> None:
    scorer = BiomarkerPriorityScorer()
    total = scorer.compute_total_score(
        disease_burden=_component(100),
        molecular_evidence=_component(100),
        clinical_evidence=_component(100),
        detection_feasibility=_component(100),
        sensor_compatibility=_component(100),
        data_confidence=_component(100),
    )
    assert total == 100.0


def test_compute_total_score_all_zero() -> None:
    scorer = BiomarkerPriorityScorer()
    total = scorer.compute_total_score(
        disease_burden=_component(0),
        molecular_evidence=_component(0),
        clinical_evidence=_component(0),
        detection_feasibility=_component(0),
        sensor_compatibility=_component(0),
        data_confidence=_component(0),
    )
    assert total == 0.0


def test_compute_total_score_weighted_combination() -> None:
    scorer = BiomarkerPriorityScorer()
    total = scorer.compute_total_score(
        disease_burden=_component(80),
        molecular_evidence=_component(60),
        clinical_evidence=_component(40),
        detection_feasibility=_component(90),
        sensor_compatibility=_component(70),
        data_confidence=_component(50),
    )
    expected = 0.25 * 80 + 0.20 * 60 + 0.20 * 40 + 0.15 * 90 + 0.10 * 70 + 0.10 * 50
    assert total == round(expected, 2)


def test_build_returns_priority_score_with_all_components() -> None:
    scorer = BiomarkerPriorityScorer()
    result = scorer.build(
        biomarker_name="KRAS G12D mutation",
        cancer_type="lung",
        disease_burden=_component(80),
        molecular_evidence=_component(60),
        clinical_evidence=_component(40, missing=True),
        detection_feasibility=_component(90),
        sensor_compatibility=_component(70),
        data_confidence=_component(50),
    )
    assert result.biomarker_name == "KRAS G12D mutation"
    assert result.cancer_type == "lung"
    assert result.missing_data_factors == ["clinical_evidence"]
    assert result.total_score > 0


def test_rate_to_score_scales_against_cap() -> None:
    score, missing = rate_to_score(50.0, cap=100.0)
    assert score == 50.0
    assert missing is False


def test_rate_to_score_clamps_above_cap() -> None:
    score, missing = rate_to_score(150.0, cap=100.0)
    assert score == 100.0
    assert missing is False


def test_rate_to_score_none_is_missing() -> None:
    score, missing = rate_to_score(None, cap=100.0)
    assert score == 0.0
    assert missing is True


def test_count_to_score_saturates() -> None:
    score, missing = count_to_score(10, saturating_at=5)
    assert score == 100.0
    assert missing is False


def test_count_to_score_zero_is_not_missing() -> None:
    score, missing = count_to_score(0, saturating_at=5)
    assert score == 0.0
    assert missing is False


def test_count_to_score_none_is_missing() -> None:
    score, missing = count_to_score(None, saturating_at=5)
    assert score == 0.0
    assert missing is True


def test_fraction_to_score() -> None:
    score, missing = fraction_to_score(0.85)
    assert score == 85.0
    assert missing is False


def test_fraction_to_score_none_is_missing() -> None:
    score, missing = fraction_to_score(None)
    assert score == 0.0
    assert missing is True
