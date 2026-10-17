"""Domain model for the Molecular Recognition Engine (Phase 1).

Enumerates all 5 documented recognition strategies but Phase 1 only computes
real compatibility for DNA hybridization and CRISPR-Cas (the two required for
the mutation/ctDNA dimension). The other three return a `NOT_YET_SUPPORTED`
recommendation rather than a guessed score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class RecognitionStrategyType(StrEnum):
    DNA_HYBRIDIZATION = "dna_hybridization"
    CRISPR_CAS = "crispr_cas"
    APTAMER = "aptamer_based"
    ANTIBODY = "antibody_based"
    AFFINITY_BASED = "affinity_based"

    @property
    def is_phase1_supported(self) -> bool:
        return self in (
            RecognitionStrategyType.DNA_HYBRIDIZATION,
            RecognitionStrategyType.CRISPR_CAS,
        )


@dataclass(frozen=True)
class RecognitionRecommendation:
    strategy: RecognitionStrategyType
    status: str  # "scored" | "not_yet_supported" | "insufficient_evidence"
    compatibility_score: float | None  # 0-100, None if not scored
    rationale: str
    supporting_evidence: list[str] = field(default_factory=list)  # human-readable refs
    limitations: list[str] = field(default_factory=list)
    confidence: float | None = None  # 0-1, None if not scored
    computation_basis: dict[str, float | int | str | bool] = field(default_factory=dict)
    # Phase 2 addition: distinguishes pure heuristic scoring from heuristic
    # scoring that additionally has real, live-fetched literature citations
    # attached (see molecular_recognition_service.attach_literature_citations).
    # Never implies curated/structured experimental evidence either way.
    evidence_source: str = "HEURISTIC"  # "HEURISTIC" | "HEURISTIC_WITH_CITATIONS"
    citation_evidence: list = field(default_factory=list)  # list[EvidenceRef]
