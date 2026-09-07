"""Domain model for the composite R&D compatibility/ranking score (Phase 1).

The score combines six weighted 0-100 factors — molecular fit, recognition
feasibility, sensor feasibility, published evidence, clinical relevance, and
data confidence — mirroring the existing BiomarkerPriorityScore pattern
(domain/entities/priority_score.py) so the two scoring systems stay legible
side by side. Every factor shows its `basis` string; nothing here is a black
box, and nothing is an invented accuracy/performance number.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RdScoreFactor:
    score: float  # 0-100
    basis: str  # human-readable explanation of how this number was derived
    missing_data: bool = False


@dataclass(frozen=True)
class RdCompositeScore:
    biomarker_name: str
    molecular_fit: RdScoreFactor
    recognition_feasibility: RdScoreFactor
    sensor_feasibility: RdScoreFactor
    published_evidence: RdScoreFactor
    clinical_relevance: RdScoreFactor
    data_confidence: RdScoreFactor
    weights: dict[str, float]  # factor name -> weight, sums to 1.0
    total_score: float  # 0-100, weighted sum

    @property
    def components(self) -> dict[str, RdScoreFactor]:
        return {
            "molecular_fit": self.molecular_fit,
            "recognition_feasibility": self.recognition_feasibility,
            "sensor_feasibility": self.sensor_feasibility,
            "published_evidence": self.published_evidence,
            "clinical_relevance": self.clinical_relevance,
            "data_confidence": self.data_confidence,
        }

    @property
    def missing_data_factors(self) -> list[str]:
        return [name for name, c in self.components.items() if c.missing_data]
