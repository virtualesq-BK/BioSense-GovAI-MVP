"""Molecular Recognition Engine (Phase 1: DNA hybridization + CRISPR-Cas only).

Input: a `MolecularCharacterizationResult` (biomarker molecular characteristics)
plus the Postgres `biomarker_recognition_matches` graph for that biomarker.
Output: one `RecognitionRecommendation` per strategy in the full 5-strategy
enum — DNA hybridization and CRISPR-Cas are scored from real inputs (an
existing graph match_score/mechanism row, or a structured fallback derived
from mutation-dimension characteristics); the other three strategies always
return `not_yet_supported` for Phase 1, never a guessed score.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

from biosense.domain.entities.biomarker_dimension import BiomarkerDimensionType, EvidenceRef
from biosense.domain.entities.molecular_characterization import (
    INSUFFICIENT_EVIDENCE,
    MolecularCharacterizationResult,
)
from biosense.domain.entities.molecular_detectability import MolecularDetectabilityResult
from biosense.domain.entities.molecular_recognition import (
    RecognitionRecommendation,
    RecognitionStrategyType,
)
from biosense.domain.entities.recognition_compatibility import RecognitionCompatibilityTable
from biosense.infrastructure.persistence.postgres.models import BiomarkerRecognitionMatch

_NOT_YET_SUPPORTED_RATIONALE = (
    "Recognition strategy not yet implemented in this platform (Phase 1 covers "
    "DNA hybridization and CRISPR-Cas only). This is a documented, real recognition "
    "class — it is deliberately left unscored rather than estimated."
)


class MolecularRecognitionEngine:
    def __init__(self, *, compatibility: RecognitionCompatibilityTable | None = None) -> None:
        self._compatibility = compatibility or RecognitionCompatibilityTable()

    def recommend(
        self,
        characterization: MolecularCharacterizationResult,
        *,
        graph_matches: list[BiomarkerRecognitionMatch],
        detectability: MolecularDetectabilityResult | None = None,
        _exclude_evidence_source: str | None = None,
    ) -> list[RecognitionRecommendation]:
        """Biomarker -> Molecular Characteristics -> Detectability ->
        Recognition Strategy. `characterization` and (optionally)
        `detectability` are both real upstream products of the same
        biomarker; nothing here bypasses them to look at biomarker
        type/name alone. The compatibility reference table
        (`recognition_compatibility.py`) documents, per dimension/strategy
        pair, the evidence level backing that pairing existing at all —
        used here only to annotate rationale, not to alter the underlying
        score math which stays keyed to real graph/characterization inputs.

        `_exclude_evidence_source` is a private hook used by
        `counterfactual_recommend` (see below) to mask one evidence source
        and recompute — never used by normal callers.
        """
        matches_by_code = {
            m.recognition_strategy.code: m
            for m in graph_matches
            if m.recognition_strategy is not None
        }

        working_characterization = characterization
        if _exclude_evidence_source is not None:
            working_characterization = self._mask_evidence_source(
                characterization, _exclude_evidence_source
            )

        results: list[RecognitionRecommendation] = []
        for strategy in RecognitionStrategyType:
            if not strategy.is_phase1_supported:
                dimension = self._dimension_of(working_characterization)
                rule = self._compatibility.rule_for(dimension, strategy) if dimension else None
                rationale = _NOT_YET_SUPPORTED_RATIONALE
                if rule is not None:
                    rationale += (
                        f" Reference compatibility ({rule.evidence_level.value}, source: "
                        f"{rule.source}): {rule.rationale}"
                    )
                results.append(
                    RecognitionRecommendation(
                        strategy=strategy,
                        status="not_yet_supported",
                        compatibility_score=None,
                        rationale=rationale,
                        supporting_evidence=[],
                        limitations=[_NOT_YET_SUPPORTED_RATIONALE],
                        confidence=None,
                    )
                )
                continue
            results.append(
                self._score_phase1_strategy(strategy, working_characterization, matches_by_code)
            )
        return results

    def counterfactual_recommend(
        self,
        characterization: MolecularCharacterizationResult,
        *,
        graph_matches: list[BiomarkerRecognitionMatch],
        exclude_evidence_source: str,
    ) -> list[RecognitionRecommendation]:
        """First-pass explainability scaffold: recompute recognition ranking
        with one evidence source (matched by `EvidenceRef.source`, e.g.
        "PubMed" or "NCI GDC") masked out, so callers can see what would be
        next-best without it. This is a simple re-run over real inputs with
        one source removed — not a causal/counterfactual model, and not a
        polished feature; it exists as a foundation for future explainable-AI
        work.
        """
        return self.recommend(
            characterization,
            graph_matches=graph_matches,
            _exclude_evidence_source=exclude_evidence_source,
        )

    @staticmethod
    def _mask_evidence_source(
        characterization: MolecularCharacterizationResult, source: str
    ) -> MolecularCharacterizationResult:
        filtered_evidence = [e for e in characterization.evidence if e.source != source]
        return replace(characterization, evidence=filtered_evidence)

    async def attach_crispr_citations(
        self,
        recommendations: list[RecognitionRecommendation],
        *,
        gene_symbol: str | None,
        pubmed=None,
        include_citations: bool = True,
    ) -> list[RecognitionRecommendation]:
        """Phase 2 Step 7: attach REAL, live-fetched PubMed citations to the
        CRISPR-Cas recommendation. Never fabricates LOD/sensitivity/specificity
        or any structured relationship data — only PMID/DOI/title/date, exactly
        as returned by the PubMed E-utilities client (see infrastructure/
        external/pubmed_client.py). If nothing relevant is found, the
        recommendation's evidence_source stays "HEURISTIC" and this is stated
        explicitly, never silently.

        `include_citations=False` is a small hook for an "evidence sensitivity
        analysis" (see counterfactual_recommend) that masks the literature-
        citation evidence category entirely, so callers can compare a
        recommendation with vs. without it — not a causal/explanatory model.
        """
        if not include_citations:
            return list(recommendations)
        if pubmed is None:
            from biosense.infrastructure.external.pubmed_client import PubmedClient

            pubmed = PubmedClient()

        out: list[RecognitionRecommendation] = []
        for rec in recommendations:
            if rec.strategy is not RecognitionStrategyType.CRISPR_CAS or not gene_symbol:
                out.append(rec)
                continue

            query = f"{gene_symbol} AND CRISPR AND detection"
            try:
                papers = await pubmed.search_and_fetch(query, max_results=3)
            except Exception:
                papers = []

            if not papers:
                out.append(
                    replace(
                        rec,
                        evidence_source="HEURISTIC",
                        rationale=rec.rationale
                        + " No relevant CRISPR-Cas literature citations were found for "
                        f"'{gene_symbol}' — evidence_source remains HEURISTIC.",
                    )
                )
                continue

            today = date.today().isoformat()
            citations = [
                EvidenceRef(
                    source="PubMed",
                    external_id=p.external_id,
                    title=p.title,
                    original_identifier=p.doi or p.external_id,
                    access_date=today,
                    access_level="public",
                    evidence_type="literature_citation",
                )
                for p in papers
            ]
            out.append(
                replace(
                    rec,
                    evidence_source="HEURISTIC_WITH_CITATIONS",
                    citation_evidence=citations,
                    rationale=rec.rationale
                    + f" Supported by {len(citations)} real literature citation(s) found via "
                    "PubMed (heuristic scoring with citations attached, not curated "
                    "structured evidence).",
                )
            )
        return out

    @staticmethod
    def _dimension_of(
        characterization: MolecularCharacterizationResult,
    ) -> BiomarkerDimensionType | None:
        try:
            return BiomarkerDimensionType(characterization.dimension)
        except ValueError:
            return None

    def _score_phase1_strategy(
        self,
        strategy: RecognitionStrategyType,
        characterization: MolecularCharacterizationResult,
        matches_by_code: dict[str, BiomarkerRecognitionMatch],
    ) -> RecognitionRecommendation:
        match = matches_by_code.get(strategy.value)
        if match is not None:
            score = float(match.match_score) * 100.0
            basis = {
                "source": "biomarker_recognition_matches (domain graph)",
                "match_score": float(match.match_score),
            }
            return RecognitionRecommendation(
                strategy=strategy,
                status="scored",
                compatibility_score=round(score, 2),
                rationale=(
                    match.mechanism
                    or f"Domain-graph match score for {strategy.value} on this biomarker."
                ),
                supporting_evidence=[
                    f"{e.source}:{e.external_id} — {e.title}" for e in characterization.evidence
                ],
                limitations=[
                    "Compatibility score reflects curated domain-graph data, not a direct "
                    "wet-lab measurement — experimental validation is required."
                ],
                confidence=0.7,
                computation_basis=basis,
            )

        # No curated graph match: derive a conservative, evidence-only estimate from
        # what molecular characterization actually established. Never invent a number
        # when there is nothing to base it on.
        detectable = (
            characterization.detectability.is_detectable_in_ctdna
            if characterization.detectability
            else None
        )
        has_gene_evidence = bool(characterization.evidence)

        if detectable is None and not has_gene_evidence:
            return RecognitionRecommendation(
                strategy=strategy,
                status="insufficient_evidence",
                compatibility_score=None,
                rationale=(
                    f"{INSUFFICIENT_EVIDENCE} to compute {strategy.value} compatibility — "
                    "no domain-graph match and no molecular characterization evidence."
                ),
                supporting_evidence=[],
                limitations=[INSUFFICIENT_EVIDENCE],
                confidence=None,
            )

        # Structured, transparent rule: a mutation-dimension biomarker with confirmed
        # ctDNA detectability and at least one literature/GDC evidence record is
        # sequence-specific by construction, which both DNA hybridization (requires a
        # known complementary sequence) and CRISPR-Cas (requires a guide-RNA-targetable
        # sequence) directly depend on. Points awarded only for factors actually present.
        basis: dict[str, float | int | str | bool] = {
            "detectable_in_ctdna": bool(detectable),
            "gene_level_evidence_count": len(characterization.evidence),
            "mutation_count": (
                characterization.detectability.mutation_count
                if characterization.detectability
                else None
            ),
        }
        points = 0
        if detectable:
            points += 50
        if has_gene_evidence:
            points += min(30, 10 * len(characterization.evidence))
        if characterization.detectability and (characterization.detectability.mutation_count or 0) > 0:
            points += 10
        score = min(90.0, float(points))  # capped below graph-curated scores; this is a heuristic

        return RecognitionRecommendation(
            strategy=strategy,
            status="scored",
            compatibility_score=round(score, 2),
            rationale=(
                f"Heuristic estimate from molecular characterization only (no curated "
                f"domain-graph match for {strategy.value} on this biomarker): "
                f"detectable_in_ctdna={bool(detectable)}, "
                f"evidence_records={len(characterization.evidence)}."
            ),
            supporting_evidence=[
                f"{e.source}:{e.external_id} — {e.title}" for e in characterization.evidence
            ],
            limitations=[
                "No curated domain-graph compatibility record exists for this "
                f"biomarker/{strategy.value} pair — this score is a transparent heuristic "
                "over real inputs, not a curated or experimental value. Requires wet-lab "
                "validation.",
            ],
            confidence=0.3,
            computation_basis=basis,
        )
