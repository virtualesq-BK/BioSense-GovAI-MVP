"""Combine six evidence-based ScoreComponents into one Biomarker Priority Score.

    Biomarker Priority Score =
        Disease Burden Score
        + Molecular Evidence Score
        + Clinical Evidence Score
        + Detection Feasibility Score
        + Sensor Compatibility Score
        + Data Confidence Score

Each component is already normalized to 0-100 by whoever builds it (see
BiomarkerPriorityService for the real evidence-gathering); this module only owns the
weighting and the missing-data-aware combination — kept separate and pure so the
weights and the arithmetic are unit-testable without any database or API access.
"""

from __future__ import annotations

from biosense.domain.entities.priority_score import BiomarkerPriorityScore, ScoreComponent


class PriorityWeights:
    """Weights sum to 1.0; each is applied to that factor's 0-100 score."""

    disease_burden: float = 0.25
    molecular_evidence: float = 0.20
    clinical_evidence: float = 0.20
    detection_feasibility: float = 0.15
    sensor_compatibility: float = 0.10
    data_confidence: float = 0.10


class BiomarkerPriorityScorer:
    def __init__(self, weights: PriorityWeights | None = None) -> None:
        self._w = weights or PriorityWeights()

    def compute_total_score(
        self,
        *,
        disease_burden: ScoreComponent,
        molecular_evidence: ScoreComponent,
        clinical_evidence: ScoreComponent,
        detection_feasibility: ScoreComponent,
        sensor_compatibility: ScoreComponent,
        data_confidence: ScoreComponent,
    ) -> float:
        weighted = (
            self._w.disease_burden * disease_burden.score
            + self._w.molecular_evidence * molecular_evidence.score
            + self._w.clinical_evidence * clinical_evidence.score
            + self._w.detection_feasibility * detection_feasibility.score
            + self._w.sensor_compatibility * sensor_compatibility.score
            + self._w.data_confidence * data_confidence.score
        )
        return round(min(max(weighted, 0.0), 100.0), 2)

    def build(
        self,
        *,
        biomarker_name: str,
        cancer_type: str,
        disease_burden: ScoreComponent,
        molecular_evidence: ScoreComponent,
        clinical_evidence: ScoreComponent,
        detection_feasibility: ScoreComponent,
        sensor_compatibility: ScoreComponent,
        data_confidence: ScoreComponent,
    ) -> BiomarkerPriorityScore:
        total = self.compute_total_score(
            disease_burden=disease_burden,
            molecular_evidence=molecular_evidence,
            clinical_evidence=clinical_evidence,
            detection_feasibility=detection_feasibility,
            sensor_compatibility=sensor_compatibility,
            data_confidence=data_confidence,
        )
        return BiomarkerPriorityScore(
            biomarker_name=biomarker_name,
            cancer_type=cancer_type,
            total_score=total,
            disease_burden=disease_burden,
            molecular_evidence=molecular_evidence,
            clinical_evidence=clinical_evidence,
            detection_feasibility=detection_feasibility,
            sensor_compatibility=sensor_compatibility,
            data_confidence=data_confidence,
        )


def rate_to_score(rate: float | None, *, cap: float) -> tuple[float, bool]:
    """Linearly scale a real-world rate to 0-100 against an explicit, documented cap.

    Returns (score, missing_data). This is a heuristic scale, not a clinical
    threshold — the cap is a normalization choice, not a claim about disease severity.
    """
    if rate is None:
        return 0.0, True
    return round(min(max(rate, 0.0), cap) / cap * 100.0, 2), False


def count_to_score(count: int | None, *, saturating_at: int) -> tuple[float, bool]:
    """Scale an evidence count (papers, mutations...) to 0-100, saturating at a cap."""
    if count is None:
        return 0.0, True
    if count <= 0:
        return 0.0, False
    return round(min(count, saturating_at) / saturating_at * 100.0, 2), False


def fraction_to_score(fraction: float | None) -> tuple[float, bool]:
    """Scale an already-0-1 fraction (match_score, efficiency...) to 0-100."""
    if fraction is None:
        return 0.0, True
    return round(min(max(fraction, 0.0), 1.0) * 100.0, 2), False
