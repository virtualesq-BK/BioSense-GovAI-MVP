from biosense.application.services.feature_extraction_service import FeatureExtractionService
from biosense.domain.entities.recommendation import RecommendationInput


def test_feature_extraction_includes_biomarker_hints() -> None:
    inp = RecommendationInput(
        cancer_type="colorectal",
        ctdna_class="mutation",
        region_code="KR-11",
        patient_age=55,
        biomarker_name="KRAS G12D mutation",
    )
    features = FeatureExtractionService().extract(inp, public_health_score=0.7)
    assert features.cancer_type == "colorectal"
    assert "KRAS" in features.biomarker_hints[0] or "KRAS" in str(features.biomarker_hints)
    assert features.age_risk_factor == 0.75
    assert "colorectal" in features.query_text


def test_age_risk_elderly() -> None:
    inp = RecommendationInput(
        cancer_type="lung",
        ctdna_class="mutation",
        region_code="KR-11",
        patient_age=72,
    )
    features = FeatureExtractionService().extract(inp)
    assert features.age_risk_factor == 1.0
