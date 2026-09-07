"""Canonical ontology synonym/abbreviation table (Phase 1 — lightweight pass).

Distinct from `domain.services.normalization` (which does deterministic
alias->code resolution for pipeline routing): this table exists to answer
"what does this abbreviation mean, and per what source" for the six Phase 1
entity types (Cancer, Gene, Mutation, Biomarker, Sensor,
RecognitionMechanism), each row citing the authority it comes from. It is
intentionally a flat table, not a graph — see domain/entities/ontology.py for
why the shape still supports a future graph layer without a rewrite.

Every citation below points to a real, publicly maintained nomenclature
authority (HGNC, WHO ICD-O-3, NCI Thesaurus, COSMIC/HGVS convention) — none of
these are invented per-mapping papers.
"""

from __future__ import annotations

from biosense.domain.entities.ontology import OntologyEntityType, OntologyMapping

_MAPPINGS: tuple[OntologyMapping, ...] = (
    OntologyMapping(
        entity_type=OntologyEntityType.CANCER,
        canonical_name="non-small cell lung cancer",
        synonyms=("NSCLC", "lung adenocarcinoma", "lung carcinoma", "폐암"),
        source_citation="WHO ICD-O-3 morphology/topography coding standard",
    ),
    OntologyMapping(
        entity_type=OntologyEntityType.CANCER,
        canonical_name="colorectal cancer",
        synonyms=("CRC", "colon cancer", "rectal cancer", "대장암"),
        source_citation="WHO ICD-O-3 morphology/topography coding standard",
    ),
    OntologyMapping(
        entity_type=OntologyEntityType.CANCER,
        canonical_name="breast cancer",
        synonyms=("breast carcinoma", "유방암"),
        source_citation="WHO ICD-O-3 morphology/topography coding standard",
    ),
    OntologyMapping(
        entity_type=OntologyEntityType.CANCER,
        canonical_name="hepatocellular carcinoma",
        synonyms=("HCC", "liver cancer", "간암"),
        source_citation="WHO ICD-O-3 morphology/topography coding standard",
    ),
    OntologyMapping(
        entity_type=OntologyEntityType.GENE,
        canonical_name="TP53",
        synonyms=("P53",),
        source_citation="HGNC gene nomenclature database",
    ),
    OntologyMapping(
        entity_type=OntologyEntityType.GENE,
        canonical_name="ERBB2",
        synonyms=("HER2", "NEU"),
        source_citation="HGNC gene nomenclature database",
    ),
    OntologyMapping(
        entity_type=OntologyEntityType.GENE,
        canonical_name="KIT",
        synonyms=("C-KIT",),
        source_citation="HGNC gene nomenclature database",
    ),
    OntologyMapping(
        entity_type=OntologyEntityType.GENE,
        canonical_name="KRAS",
        synonyms=("K-RAS",),
        source_citation="HGNC gene nomenclature database",
    ),
    OntologyMapping(
        entity_type=OntologyEntityType.MUTATION,
        canonical_name="KRAS G12D missense mutation",
        synonyms=("KRAS c.35G>A", "KRAS p.G12D"),
        source_citation="HGVS sequence variant nomenclature",
    ),
    OntologyMapping(
        entity_type=OntologyEntityType.MUTATION,
        canonical_name="EGFR exon 19 deletion",
        synonyms=("EGFR ex19del", "EGFR del19"),
        source_citation="HGVS sequence variant nomenclature",
    ),
    OntologyMapping(
        entity_type=OntologyEntityType.BIOMARKER,
        canonical_name="circulating tumor DNA",
        synonyms=("ctDNA", "cell-free tumor DNA"),
        source_citation="NCI Thesaurus (NCIt) biomarker terminology",
    ),
    OntologyMapping(
        entity_type=OntologyEntityType.SENSOR,
        canonical_name="electrochemical biosensor",
        synonyms=("EC sensor", "electrochemical biosensing platform"),
        source_citation="NCI Thesaurus (NCIt) biosensor device terminology",
    ),
    OntologyMapping(
        entity_type=OntologyEntityType.RECOGNITION_MECHANISM,
        canonical_name="DNA hybridization",
        synonyms=("nucleic acid hybridization", "hybridization probe capture"),
        source_citation="NCI Thesaurus (NCIt) molecular recognition terminology",
    ),
    OntologyMapping(
        entity_type=OntologyEntityType.RECOGNITION_MECHANISM,
        canonical_name="CRISPR-Cas-based recognition",
        synonyms=("CRISPR diagnostics", "Cas-mediated recognition", "CRISPR-Cas"),
        source_citation="NCI Thesaurus (NCIt) molecular recognition terminology",
    ),
)


class OntologyService:
    """Read-only lookup over the Phase 1 synonym table."""

    def __init__(self) -> None:
        self._mappings = _MAPPINGS

    def all(self) -> tuple[OntologyMapping, ...]:
        return self._mappings

    def by_entity_type(self, entity_type: OntologyEntityType) -> list[OntologyMapping]:
        return [m for m in self._mappings if m.entity_type is entity_type]

    def resolve(self, entity_type: OntologyEntityType, term: str) -> OntologyMapping | None:
        """Return the mapping whose canonical name or synonyms match `term`
        case-insensitively, or None if this table has no entry for it — never
        guesses a canonical form it doesn't have a citation for.
        """
        if not term:
            return None
        needle = term.strip().lower()
        for m in self._mappings:
            if m.entity_type is not entity_type:
                continue
            if needle == m.canonical_name.lower() or needle in (s.lower() for s in m.synonyms):
                return m
        return None
