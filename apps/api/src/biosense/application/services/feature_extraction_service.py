import structlog

from biosense.domain.entities.recommendation import (
    ExtractedFeatures,
    PublicHealthSnapshot,
    RecommendationInput,
)

logger = structlog.get_logger()

_CANCER_NAME_KO: dict[str, str] = {
    "lung": "폐암",
    "colorectal": "대장암",
    "breast": "유방암",
    "liver": "간암",
    "stomach": "위암",
    "pancreatic": "췌장암",
    "ovarian": "난소암",
    "prostate": "전립선암",
    "other": "암",
    # UI aliases
    "CRC": "대장암",
    "LUNG": "폐암",
    "BREAST": "유방암",
    "LIVER": "간암",
}

_SIMILAR_THRESHOLD_PCT = 5.0


class FeatureExtractionService:
    """Extract structured features from clinical input."""

    def extract(
        self,
        inp: RecommendationInput,
        *,
        incidence_rate: float | None = None,
        mortality_rate: float | None = None,
        public_health_score: float = 0.5,
        national_incidence_avg: float | None = None,
        national_mortality_avg: float | None = None,
        region_name_ko: str | None = None,
        public_health: PublicHealthSnapshot | None = None,
    ) -> ExtractedFeatures:
        if public_health is not None:
            incidence_rate = public_health.incidence_rate
            mortality_rate = public_health.mortality_rate
            public_health_score = public_health.public_health_score
            national_incidence_avg = public_health.national_incidence_avg
            national_mortality_avg = public_health.national_mortality_avg
            region_name_ko = public_health.region_name_ko or region_name_ko

        age_risk = _age_risk_factor(inp.patient_age)
        hints = _biomarker_hints(inp)

        query_text = (
            f"{inp.cancer_type} cancer ctDNA {inp.ctdna_class} biomarker biosensor "
            f"region {inp.region_code} age {inp.patient_age}"
        )
        if inp.biomarker_name:
            query_text += f" {inp.biomarker_name}"
        if inp.notes:
            query_text += f" {inp.notes}"

        narrative = build_public_health_narrative(
            region_name_ko=region_name_ko,
            cancer_type=inp.cancer_type,
            patient_age=inp.patient_age,
            incidence_rate=incidence_rate,
            mortality_rate=mortality_rate,
            national_incidence_avg=national_incidence_avg,
            national_mortality_avg=national_mortality_avg,
        )

        features = ExtractedFeatures(
            cancer_type=inp.cancer_type,
            ctdna_class=inp.ctdna_class,
            region_code=inp.region_code,
            patient_age=inp.patient_age,
            incidence_rate=incidence_rate,
            mortality_rate=mortality_rate,
            age_risk_factor=age_risk,
            public_health_score=public_health_score,
            query_text=query_text.strip(),
            biomarker_hints=hints,
            public_health_narrative=narrative,
            national_incidence_avg=national_incidence_avg,
            national_mortality_avg=national_mortality_avg,
            region_name_ko=region_name_ko,
        )
        logger.info(
            "features_extracted",
            cancer=inp.cancer_type,
            ctdna=inp.ctdna_class,
            has_narrative=bool(narrative),
        )
        return features


def build_public_health_narrative(
    *,
    region_name_ko: str | None,
    cancer_type: str,
    patient_age: int,
    incidence_rate: float | None,
    mortality_rate: float | None,
    national_incidence_avg: float | None,
    national_mortality_avg: float | None,
) -> str:
    """Rule-based Korean priority sentence; empty when inputs are insufficient."""
    region = (region_name_ko or "").strip()
    cancer_ko = _CANCER_NAME_KO.get(cancer_type, _CANCER_NAME_KO.get(cancer_type.lower(), "암"))
    if not region:
        return ""

    metric_label, regional, national = _pick_comparison_metric(
        incidence_rate, mortality_rate, national_incidence_avg, national_mortality_avg
    )
    if regional is None or national is None or national <= 0:
        return ""

    pct = round(abs((regional - national) / national) * 100.0)
    age_band = _age_band_ko(patient_age)
    subject = f"{region} {age_band}{cancer_ko}".replace("  ", " ").strip()

    if pct < _SIMILAR_THRESHOLD_PCT:
        return (
            f"{subject} {metric_label}이 전국 평균과 유사하여 "
            f"표준 선별과 병행해 혈액 기반 조기진단 전략을 검토함"
        )

    direction = "높아" if regional > national else "낮아"
    priority = (
        "혈액 기반 조기진단 전략이 우선 검토됨"
        if regional > national
        else "표준 선별검사와 병행 검토됨"
    )
    return (
        f"{subject} 부담이 전국 평균 대비 {pct}% {direction} {priority}"
    )


def _pick_comparison_metric(
    incidence_rate: float | None,
    mortality_rate: float | None,
    national_incidence_avg: float | None,
    national_mortality_avg: float | None,
) -> tuple[str, float | None, float | None]:
    if incidence_rate is not None and national_incidence_avg is not None:
        return "발생률", incidence_rate, national_incidence_avg
    if mortality_rate is not None and national_mortality_avg is not None:
        return "사망률", mortality_rate, national_mortality_avg
    return "발생률", None, None


def _age_band_ko(age: int) -> str:
    if age >= 65:
        return "고령층 "
    if age >= 40:
        return "중장년층 "
    return ""


def _age_risk_factor(age: int) -> float:
    if age < 18:
        return 0.3
    if age < 40:
        return 0.5
    if age < 65:
        return 0.75
    return 1.0


def _biomarker_hints(inp: RecommendationInput) -> list[str]:
    hints: list[str] = []
    if inp.biomarker_name:
        hints.append(inp.biomarker_name)
    ctdna_gene_map = {
        "mutation": ["KRAS", "EGFR", "TP53"],
        "methylation": ["SEPT9", "BRCA1"],
        "fragmentomics": ["fragment"],
        "cnv": ["copy number"],
        "exosomal_mirna": ["miR-21", "miR-141", "miR-1246"],
        "ctc": ["EpCAM", "CTC"],
        "multi_omics": ["multi-omics", "panel"],
    }
    hints.extend(ctdna_gene_map.get(inp.ctdna_class, []))
    return hints
