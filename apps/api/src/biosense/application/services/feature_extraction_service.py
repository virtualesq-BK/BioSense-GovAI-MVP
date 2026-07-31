import structlog

from biosense.domain.entities.recommendation import ExtractedFeatures, RecommendationInput

logger = structlog.get_logger()


class FeatureExtractionService:
    """Extract structured features from clinical input."""

    def extract(
        self,
        inp: RecommendationInput,
        *,
        incidence_rate: float | None = None,
        mortality_rate: float | None = None,
        public_health_score: float = 0.5,
    ) -> ExtractedFeatures:
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
        )
        logger.info("features_extracted", cancer=inp.cancer_type, ctdna=inp.ctdna_class)
        return features


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
    }
    hints.extend(ctdna_gene_map.get(inp.ctdna_class, []))
    return hints
