"""Domain output of the Molecular Detectability module (Phase 1.5).

Distinct from `molecular_characterization.py`: characterization answers
"what does the biomarker molecularly look like" (does it exist, what is it),
while this module answers "given that, can an assay/sensor actually detect
it" — abundance, allele fraction, sequence/chemical distinguishability,
structural signal, sample compatibility, background interference.

Every attribute is `"unknown"` (for string fields) or `None` (for numeric
fields) unless there is real, attributable data behind it — never a fabricated
number. `detectability_confidence` is derived from how many of the other
attributes are actually known, not asserted independently.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from biosense.domain.entities.biomarker_dimension import EvidenceRef

UNKNOWN = "unknown"


@dataclass(frozen=True)
class MolecularDetectabilityResult:
    biomarker: str
    dimension: str

    # Quantitative/structured attributes — None when not backed by real data.
    abundance: float | None  # e.g. mutation_count as a proxy for observed abundance in records
    allele_fraction: float | None  # variant allele fraction, when reported
    sequence_specificity: str  # "unknown" or a description backed by evidence
    chemical_distinguishability: str  # "unknown" or a description backed by evidence
    structural_signal: str  # "unknown" or a description backed by evidence
    sample_compatibility: str  # "unknown" or e.g. "ctDNA (plasma)" when established
    background_interference: str  # "unknown" or a description backed by evidence

    # 0-1, derived from the fraction of the above attributes that are actually
    # known (not "unknown"/None) — never asserted independently of that count.
    detectability_confidence: float

    basis: str  # explanation of how detectability_confidence was computed
    evidence: list[EvidenceRef] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "biomarker": self.biomarker,
            "dimension": self.dimension,
            "abundance": self.abundance,
            "allele_fraction": self.allele_fraction,
            "sequence_specificity": self.sequence_specificity,
            "chemical_distinguishability": self.chemical_distinguishability,
            "structural_signal": self.structural_signal,
            "sample_compatibility": self.sample_compatibility,
            "background_interference": self.background_interference,
            "detectability_confidence": self.detectability_confidence,
            "basis": self.basis,
            "evidence": [
                {"source": e.source, "external_id": e.external_id, "title": e.title}
                for e in self.evidence
            ],
            "limitations": list(self.limitations),
        }
