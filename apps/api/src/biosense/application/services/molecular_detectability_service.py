"""Molecular Detectability module (Phase 1.5).

Consumes a `MolecularCharacterizationResult` (already built from real
Biomarker/GDC/literature inputs — see molecular_characterization_service.py)
and derives a `MolecularDetectabilityResult` from the *same* real fields.
This module invents nothing: any attribute we cannot ground in the
characterization's own `detectability`/`evidence`/`molecular_characteristics`
is left `"unknown"` / `None`.
"""

from __future__ import annotations

from biosense.domain.entities.biomarker_dimension import BiomarkerEvidenceStatus
from biosense.domain.entities.molecular_characterization import MolecularCharacterizationResult
from biosense.domain.entities.molecular_detectability import UNKNOWN, MolecularDetectabilityResult

# The set of attributes we can, in principle, ever populate from the current
# real inputs. Used only to compute what fraction are actually known — not a
# claim that all seven are equally important.
_TRACKED_ATTRS = 7


class MolecularDetectabilityService:
    def assess(
        self, characterization: MolecularCharacterizationResult
    ) -> MolecularDetectabilityResult:
        det = characterization.detectability

        abundance = float(det.mutation_count) if det and det.mutation_count is not None else None
        # Allele fraction is not sourced anywhere in the current pipeline
        # (would require variant-call-level GDC/VCF data we do not fetch) —
        # honestly unknown rather than guessed.
        allele_fraction = None

        has_gene_evidence = bool(characterization.evidence)
        sequence_specificity = (
            f"Sequence-level target established via {len(characterization.evidence)} linked "
            "evidence record(s) (gene/mutation identity known)."
            if has_gene_evidence
            else UNKNOWN
        )

        chemical_distinguishability = (
            "Point-mutation/base-change target — chemically distinguishable from wild-type "
            "sequence by design (hybridization/PCR-class assays)."
            if det and det.is_detectable_in_ctdna
            else UNKNOWN
        )

        # No structural (e.g. protein-domain, secondary-structure) data source
        # is wired into Phase 1 characterization, so this stays unknown.
        structural_signal = UNKNOWN

        sample_compatibility = UNKNOWN
        if det and det.is_detectable_in_ctdna:
            sample_compatibility = "circulating tumor DNA (ctDNA), plasma"
        elif characterization.dimension == "methylation":
            # Metadata-only integration (Phase 2): derive sample compatibility
            # only from the GDC file-metadata sentence already assembled in
            # characterization.specificity_features — never fabricated.
            marker = "Sample types observed in GDC file metadata: "
            found = next(
                (f for f in characterization.specificity_features if f.startswith(marker)),
                None,
            )
            if found:
                sample_compatibility = found[len(marker):].rstrip(".")

        # No background/interferent panel data is available from current
        # sources (GDC/PubMed) — left unknown rather than assumed benign.
        background_interference = UNKNOWN

        known_count = sum(
            1
            for v in (
                abundance,
                allele_fraction,
                None if sequence_specificity == UNKNOWN else sequence_specificity,
                None if chemical_distinguishability == UNKNOWN else chemical_distinguishability,
                None if structural_signal == UNKNOWN else structural_signal,
                None if sample_compatibility == UNKNOWN else sample_compatibility,
                None if background_interference == UNKNOWN else background_interference,
            )
            if v is not None
        )
        confidence = round(known_count / _TRACKED_ATTRS, 2)

        limitations: list[str] = []
        if characterization.evidence_status == BiomarkerEvidenceStatus.INSUFFICIENT_EVIDENCE:
            limitations.append(
                "Upstream molecular characterization has insufficient evidence — "
                "detectability attributes here are correspondingly limited."
            )
        if allele_fraction is None:
            limitations.append(
                "Allele fraction unknown — Phase 1 does not ingest variant-call-level "
                "(VCF) data required to compute it."
            )
        if structural_signal == UNKNOWN:
            limitations.append(
                "Structural signal unknown — no structural/proteomic data source is wired "
                "into this pipeline yet."
            )
        if background_interference == UNKNOWN:
            limitations.append(
                "Background interference unknown — no interferent/specificity panel data "
                "source is wired into this pipeline yet."
            )

        return MolecularDetectabilityResult(
            biomarker=characterization.biomarker,
            dimension=characterization.dimension,
            abundance=abundance,
            allele_fraction=allele_fraction,
            sequence_specificity=sequence_specificity,
            chemical_distinguishability=chemical_distinguishability,
            structural_signal=structural_signal,
            sample_compatibility=sample_compatibility,
            background_interference=background_interference,
            detectability_confidence=confidence,
            basis=(
                f"{known_count}/{_TRACKED_ATTRS} detectability attributes are backed by real "
                "data from molecular characterization; the rest are honestly reported as "
                "unknown rather than estimated."
            ),
            evidence=list(characterization.evidence),
            limitations=limitations,
        )
