from biosense.application.services.feature_extraction_service import (
    FeatureExtractionService,
    build_public_health_narrative,
)
from biosense.domain.entities.recommendation import PublicHealthSnapshot, RecommendationInput


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


def test_narrative_higher_than_national_average() -> None:
    text = build_public_health_narrative(
        region_name_ko="부산광역시",
        cancer_type="stomach",
        patient_age=70,
        incidence_rate=45.8,
        mortality_rate=15.6,
        national_incidence_avg=38.0,
        national_mortality_avg=13.5,
    )
    assert "부산광역시" in text
    assert "고령층" in text
    assert "위암" in text
    assert "전국 평균 대비" in text
    assert "높아" in text
    assert "혈액 기반 조기진단" in text


def test_narrative_omitted_when_rates_missing() -> None:
    text = build_public_health_narrative(
        region_name_ko="서울특별시",
        cancer_type="lung",
        patient_age=55,
        incidence_rate=None,
        mortality_rate=None,
        national_incidence_avg=42.0,
        national_mortality_avg=27.0,
    )
    assert text == ""


def test_narrative_similar_when_within_threshold() -> None:
    text = build_public_health_narrative(
        region_name_ko="서울특별시",
        cancer_type="lung",
        patient_age=50,
        incidence_rate=42.5,
        mortality_rate=28.0,
        national_incidence_avg=42.0,
        national_mortality_avg=27.0,
    )
    assert "유사" in text
    assert "중장년층" in text


def test_extract_attaches_narrative_from_snapshot() -> None:
    inp = RecommendationInput(
        cancer_type="stomach",
        ctdna_class="mutation",
        region_code="KR-26",
        patient_age=68,
    )
    snapshot = PublicHealthSnapshot(
        incidence_rate=45.8,
        mortality_rate=15.6,
        public_health_score=0.6,
        national_incidence_avg=38.0,
        national_mortality_avg=13.5,
        region_name_ko="부산광역시",
        region_code="KR-26",
    )
    features = FeatureExtractionService().extract(inp, public_health=snapshot)
    assert features.public_health_narrative
    assert "부산광역시" in features.public_health_narrative
    assert features.national_incidence_avg == 38.0
