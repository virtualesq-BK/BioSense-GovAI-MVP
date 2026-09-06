from biosense.api.v1.catalog import _to_priority_response
from biosense.domain.entities.priority_score import BiomarkerPriorityScore, ScoreComponent


def _component(score: float = 50.0) -> ScoreComponent:
    return ScoreComponent(score=score, evidence="e", source="s", confidence=0.5)


def test_to_priority_response_converts_dataclass_components() -> None:
    priority = BiomarkerPriorityScore(
        biomarker_name="KRAS G12D mutation",
        cancer_type="lung",
        total_score=72.5,
        disease_burden=_component(80),
        molecular_evidence=_component(60),
        clinical_evidence=_component(40),
        detection_feasibility=_component(90),
        sensor_compatibility=_component(70),
        data_confidence=_component(100),
    )

    response = _to_priority_response(priority)

    assert response.biomarker_name == "KRAS G12D mutation"
    assert response.total_score == 72.5
    assert response.disease_burden.score == 80
    assert response.missing_data_factors == []
