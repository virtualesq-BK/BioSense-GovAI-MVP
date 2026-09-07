"""Domain value objects for global genomic data (NCI GDC)."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RawGdcProjectRecord:
    """A GDC project (e.g. a TCGA cancer cohort)."""

    project_id: str
    name: str
    primary_sites: list[str]
    disease_types: list[str]
    case_count: int | None
    source: str
    access_level: str = "open"


@dataclass(frozen=True)
class RawGdcGeneRecord:
    """A gene annotation from the GDC gene index."""

    gene_id: str
    symbol: str
    name: str | None
    biotype: str | None
    source: str
    access_level: str = "open"


@dataclass(frozen=True)
class RawGdcMutationRecord:
    """A simple somatic mutation (SSM) record from the GDC ssms endpoint."""

    ssm_id: str
    genomic_dna_change: str | None
    mutation_subtype: str | None
    gene_symbols: list[str] = field(default_factory=list)
    amino_acid_changes: list[str] = field(default_factory=list)
    source: str = "gdc"
    access_level: str = "open"


@dataclass(frozen=True)
class RawGdcMethylationFileRecord:
    """FILE-LEVEL metadata for a methylation array file from the GDC /files
    endpoint — verified (Phase 2 Step 0 audit, docs/data-feasibility-phase2.md)
    to expose only file/platform/case-level metadata via REST, never actual
    CpG-site IDs or beta values. This record type carries only what the API
    actually returns; do not add quantitative fields to it.
    """

    file_id: str
    file_name: str | None
    data_type: str | None  # e.g. "Methylation Beta Value"
    platform: str | None  # e.g. "Illumina Human Methylation 450"
    access: str | None  # "open" or "controlled"
    project_id: str | None  # e.g. "TCGA-LUAD"
    case_count: int | None
    sample_types: list[str] = field(default_factory=list)
    source: str = "gdc"
