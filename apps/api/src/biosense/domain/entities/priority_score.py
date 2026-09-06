"""Domain value objects for the Global Biomarker Priority Score."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreComponent:
    """One weighted factor of a BiomarkerPriorityScore.

    `missing_data=True` means this factor could not be computed from any real
    source — `score` is then 0.0, never a guessed placeholder, so the total
    score honestly reflects what evidence actually exists.
    """

    score: float  # 0-100
    evidence: str
    source: str
    confidence: float  # 0-1
    missing_data: bool = False


@dataclass(frozen=True)
class BiomarkerPriorityScore:
    """Biomarker Priority Score = weighted sum of six 0-100 evidence factors.

    Every factor carries its own evidence/source/confidence/missing_data, so the
    UI can show why a biomarker scored the way it did, not just the number.
    """

    biomarker_name: str
    cancer_type: str
    total_score: float  # 0-100
    disease_burden: ScoreComponent
    molecular_evidence: ScoreComponent
    clinical_evidence: ScoreComponent
    detection_feasibility: ScoreComponent
    sensor_compatibility: ScoreComponent
    data_confidence: ScoreComponent

    @property
    def components(self) -> dict[str, ScoreComponent]:
        return {
            "disease_burden": self.disease_burden,
            "molecular_evidence": self.molecular_evidence,
            "clinical_evidence": self.clinical_evidence,
            "detection_feasibility": self.detection_feasibility,
            "sensor_compatibility": self.sensor_compatibility,
            "data_confidence": self.data_confidence,
        }

    @property
    def missing_data_factors(self) -> list[str]:
        return [name for name, c in self.components.items() if c.missing_data]
