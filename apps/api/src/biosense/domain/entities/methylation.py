"""Domain entity for methylation biomarkers (Phase 2, METADATA-ONLY integration).

Per the Phase 2 Step 0 audit (docs/data-feasibility-phase2.md), the GDC REST
API exposes only FILE/PROJECT-LEVEL metadata for methylation — file_id,
platform, chip_id, access level, case/project linkage. There is no field for
actual CpG-site IDs or beta values via REST; those require downloading and
parsing TXT/IDAT files offline, which is explicitly out of scope for this
phase. `CpG_site` and `methylation_value` on this entity therefore stay
`None` unless/until a future bulk-processing pipeline populates them from
real parsed files — never guess or interpolate a number into them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from biosense.domain.entities.biomarker_dimension import EvidenceRef

# Canonical mapping of the 3 MVP cancer types to their TCGA project cohorts,
# used to scope GDC methylation file discovery. This mirrors whatever
# cancer-type identifiers the rest of the platform already uses (lung /
# colorectal / breast) -- verified live against the GDC /projects endpoint
# in the Step 0 audit (all 5 projects have open-access methylation files).
CANCER_TYPE_TO_TCGA_PROJECTS: dict[str, list[str]] = {
    "lung": ["TCGA-LUAD", "TCGA-LUSC"],
    "colorectal": ["TCGA-COAD", "TCGA-READ"],
    "breast": ["TCGA-BRCA"],
}


@dataclass(frozen=True)
class MethylationRecord:
    """Metadata-only methylation record. All quantitative/site-level fields
    are Optional and stay `None` unless backed by real parsed data (not yet
    implemented). File/project-level fields are populated from live GDC
    /files and /projects responses.
    """

    gene: str | None
    genomic_region: str | None
    cpg_site: str | None  # None: no beta-value/CpG-site data source is integrated
    methylation_value: float | None  # None: quantitative characterization is PLANNED, not implemented
    methylation_status: str | None  # "unknown" unless curated
    sample_type: str | None  # from GDC cases.samples.sample_type, when known
    cancer_type: str | None
    study: str | None  # e.g. "TCGA-LUAD"
    dataset: str | None  # e.g. "GDC methylation array file metadata"
    assay: str | None  # e.g. "Illumina Infinium HumanMethylation450"
    platform: str | None
    normalization_status: str | None  # "unknown" -- no normalization pipeline is run here
    units: str | None  # None unless a real quantitative unit applies
    original_field_name: str | None  # GDC field name this was sourced from, for auditability
    dataset_version: str | None
    evidence: list[EvidenceRef] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "gene": self.gene,
            "genomic_region": self.genomic_region,
            "CpG_site": self.cpg_site,
            "methylation_value": self.methylation_value,
            "methylation_status": self.methylation_status,
            "sample_type": self.sample_type,
            "cancer_type": self.cancer_type,
            "study": self.study,
            "dataset": self.dataset,
            "assay": self.assay,
            "platform": self.platform,
            "normalization_status": self.normalization_status,
            "units": self.units,
            "original_field_name": self.original_field_name,
            "dataset_version": self.dataset_version,
            "evidence": [
                {
                    "source": e.source,
                    "external_id": e.external_id,
                    "title": e.title,
                    "dataset": e.dataset,
                    "original_identifier": e.original_identifier,
                    "access_date": e.access_date,
                    "access_level": e.access_level,
                    "evidence_type": e.evidence_type,
                }
                for e in self.evidence
            ],
        }
