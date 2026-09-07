"""Biomarker dimension model (Phase 1 of the Global Multi-Omics Bio R&D Infrastructure).

Full target pipeline (staged rollout — see docs/ARCHITECTURE.md):
    Cancer -> Multi-Omics Data -> Biomarker Candidate -> Molecular Characterization
    -> Molecular Recognition Strategy -> Signal Transduction -> Biosensor Design
    -> Evidence-backed R&D Recommendation

Phase 1 implements only the "mutation" dimension (ctDNA mutation biomarkers). The
other dimensions are enumerated so later phases can slot in without a data-model
rewrite, but they are not populated here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BiomarkerDimensionType(str, Enum):
    """The multi-omics dimensions a biomarker candidate can belong to.

    Only MUTATION is implemented in Phase 1. The rest are real, documented
    biomarker classes reserved for later phases — selecting one of them should
    surface "not yet supported", never a guessed answer.
    """

    MUTATION = "mutation"
    METHYLATION = "methylation"
    EXPRESSION = "expression"
    PROTEIN = "protein"
    FUSION = "fusion"
    COPY_NUMBER = "copy_number"

    @property
    def is_phase1_supported(self) -> bool:
        return self is BiomarkerDimensionType.MUTATION


class BiomarkerEvidenceStatus(str, Enum):
    """How well-supported a characterization/recognition/scoring claim is,
    stated explicitly rather than left implicit in a bare number.

    This is orthogonal to `status` fields elsewhere ("scored" /
    "not_yet_supported" / "insufficient_evidence") which describe pipeline
    stage outcome; this enum describes evidence *strength* for a claim that
    was produced.
    """

    SUPPORTED = "supported"  # multiple independent real-data sources agree
    PARTIALLY_SUPPORTED = "partially_supported"  # at least one real source, gaps remain
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"  # no usable real-data source
    PLANNED = "planned"  # dimension/strategy not yet implemented in this platform


class EvidenceHierarchyLevel(str, Enum):
    """Lightweight INTERNAL evidence-strength ranking (Phase 2, Step 10).

    This is an internal ranking framework used only to help this platform's
    own callers/UI reason about evidence strength consistently — it is NOT an
    external scientific standard (e.g. not GRADE, not clinical evidence
    levels) and must never be presented to users as one. It complements, but
    is distinct from, `BiomarkerEvidenceStatus` (which describes whether a
    *claim this platform produced* is supported) and
    `CompatibilityEvidenceLevel` in recognition_compatibility.py (which is the
    Phase 1.5 equivalent, specific to the dimension/strategy compatibility
    table) — reuse one of those where they already fit rather than adding a
    third parallel scheme; use this enum only where neither existing one
    applies (e.g. ranking a raw EvidenceRef itself).
    """

    LEVEL_A = "level_a"  # direct experimental evidence for the specific claim
    LEVEL_B = "level_b"  # multiple independent studies, not all directly experimental
    LEVEL_C = "level_c"  # single study
    LEVEL_D = "level_d"  # indirect / related evidence only
    LEVEL_E = "level_e"  # heuristic / model-derived, not literature-sourced
    UNKNOWN = "unknown"  # insufficient information to rank


@dataclass(frozen=True)
class EvidenceRef:
    """A single citation backing a claim. Never fabricated — if there is no real
    source, omit the claim rather than inventing an EvidenceRef.

    `source`/`external_id`/`title` are the original required fields (DTO
    contract — do not rename). The remaining fields are additive/optional so
    existing callers/DTOs that only set the first three keep working
    unchanged.
    """

    source: str  # e.g. "PubMed", "NCI GDC", "HGNC"
    external_id: str
    title: str
    dataset: str | None = None  # e.g. "GDC simple somatic mutation", "PubMed abstract"
    original_identifier: str | None = None  # identifier as published by the source, if different from external_id
    access_date: str | None = None  # ISO date this record was retrieved, if known
    access_level: str | None = None  # e.g. "public", "controlled_access", "internal"
    evidence_type: str | None = None  # e.g. "genomic_record", "literature", "curated_domain_graph"


@dataclass(frozen=True)
class BiomarkerDimension:
    """Extended biomarker profile carrying the multi-omics dimension fields.

    All descriptive fields are optional (`None`) when no structured evidence
    supports them; `missing_fields` names which ones so callers/UI can render an
    honest "insufficient evidence" state instead of blank-but-implied-known.
    """

    biomarker_name: str
    biomarker_type: BiomarkerDimensionType
    molecular_feature: str | None  # e.g. "KRAS G12D missense mutation"
    genomic_context: str | None  # e.g. gene locus / chromosome / exon
    chemical_feature: str | None  # e.g. base-pair change, amino-acid substitution
    structural_feature: str | None  # e.g. protein domain affected
    detection_target: str | None  # e.g. "circulating tumor DNA (ctDNA)"
    evidence: list[EvidenceRef] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
