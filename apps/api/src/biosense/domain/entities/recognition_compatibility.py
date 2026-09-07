"""Biomarker-dimension -> recognition-strategy compatibility, as data.

This mapping is a *reference table with cited evidence levels*, not an
assertion of settled biology. Each row states its own `evidence_level`,
`source`, `rationale`, and `confidence` so the platform never presents a
compatibility claim as more certain than it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from biosense.domain.entities.biomarker_dimension import BiomarkerDimensionType
from biosense.domain.entities.molecular_recognition import RecognitionStrategyType


class CompatibilityEvidenceLevel(str, Enum):
    ESTABLISHED = "established"  # widely documented in literature/standards
    EMERGING = "emerging"  # documented but less mature / fewer sources
    THEORETICAL = "theoretical"  # plausible by mechanism, not yet broadly documented
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"  # no real literature evidence found/checked for this pairing during platform development — honestly unresolved, not a guessed rationale


@dataclass(frozen=True)
class RecognitionCompatibilityRule:
    dimension: BiomarkerDimensionType
    strategy: RecognitionStrategyType
    evidence_level: CompatibilityEvidenceLevel
    source: str
    rationale: str
    confidence: float  # 0-1, reference-level confidence in this dimension/strategy pairing existing at all


_RULES: tuple[RecognitionCompatibilityRule, ...] = (
    RecognitionCompatibilityRule(
        dimension=BiomarkerDimensionType.MUTATION,
        strategy=RecognitionStrategyType.DNA_HYBRIDIZATION,
        evidence_level=CompatibilityEvidenceLevel.ESTABLISHED,
        source="NCI Thesaurus / standard molecular diagnostics literature",
        rationale=(
            "Point mutations and small indels are directly targetable by sequence-"
            "complementary hybridization probes — a well-established recognition class "
            "for ctDNA mutation biomarkers."
        ),
        confidence=0.9,
    ),
    RecognitionCompatibilityRule(
        dimension=BiomarkerDimensionType.MUTATION,
        strategy=RecognitionStrategyType.CRISPR_CAS,
        evidence_level=CompatibilityEvidenceLevel.EMERGING,
        source="CRISPR-based diagnostics literature (e.g. SHERLOCK/DETECTR class assays)",
        rationale=(
            "CRISPR-Cas guide-RNA targeting can discriminate single-nucleotide mutations "
            "from wild-type sequence; an active but comparatively newer diagnostic class "
            "than hybridization."
        ),
        confidence=0.75,
    ),
    RecognitionCompatibilityRule(
        dimension=BiomarkerDimensionType.METHYLATION,
        strategy=RecognitionStrategyType.DNA_HYBRIDIZATION,
        evidence_level=CompatibilityEvidenceLevel.INSUFFICIENT_EVIDENCE,
        source="Not yet checked against real literature during Phase 2 development",
        rationale=(
            "Methylation-specific hybridization/qPCR assays are a documented recognition "
            "class in principle, but no real citation search or curation was performed for "
            "this specific pairing during Phase 2 — honestly marked unresolved rather than "
            "asserted. Phase 2 also only integrates GDC file/project-level methylation "
            "metadata (see molecular_characterization_service.py), not quantitative "
            "beta-value data, so this pairing is not scored at the recommendation level."
        ),
        confidence=0.0,
    ),
    RecognitionCompatibilityRule(
        dimension=BiomarkerDimensionType.METHYLATION,
        strategy=RecognitionStrategyType.CRISPR_CAS,
        evidence_level=CompatibilityEvidenceLevel.INSUFFICIENT_EVIDENCE,
        source="Not yet checked against real literature during Phase 2 development",
        rationale=(
            "CRISPR-Cas-based methylation detection (e.g. requiring bisulfite conversion or "
            "methylation-sensitive restriction as an upstream step) is not curated with real "
            "citations in this platform yet — honestly marked unresolved rather than "
            "asserted or scored."
        ),
        confidence=0.0,
    ),
    RecognitionCompatibilityRule(
        dimension=BiomarkerDimensionType.FUSION,
        strategy=RecognitionStrategyType.DNA_HYBRIDIZATION,
        evidence_level=CompatibilityEvidenceLevel.ESTABLISHED,
        source="FISH/break-apart probe literature",
        rationale=(
            "Gene-fusion breakpoints are a classic hybridization (FISH-class) target; "
            "not yet computed in this platform for lack of fusion-dimension data ingestion."
        ),
        confidence=0.6,
    ),
)


class RecognitionCompatibilityTable:
    """Read-only lookup over the compatibility reference rows."""

    def __init__(self) -> None:
        self._rules = _RULES

    def all(self) -> tuple[RecognitionCompatibilityRule, ...]:
        return self._rules

    def for_dimension(
        self, dimension: BiomarkerDimensionType
    ) -> list[RecognitionCompatibilityRule]:
        return [r for r in self._rules if r.dimension is dimension]

    def rule_for(
        self, dimension: BiomarkerDimensionType, strategy: RecognitionStrategyType
    ) -> RecognitionCompatibilityRule | None:
        for r in self._rules:
            if r.dimension is dimension and r.strategy is strategy:
                return r
        return None
