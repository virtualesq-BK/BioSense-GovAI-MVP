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
