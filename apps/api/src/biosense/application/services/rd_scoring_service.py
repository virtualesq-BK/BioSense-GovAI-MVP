"""Composite R&D compatibility/ranking scoring engine (Phase 1).

Combines molecular fit, recognition feasibility, sensor feasibility, published
evidence, clinical relevance, and data confidence into one normalized 0-100
score. Every factor's `basis` string shows exactly how it was computed — the
result is a transparent weighted sum of real, already-derived numbers (from
the Molecular Characterization / Recognition / Transduction engines and the
existing BiomarkerPriorityScore), never an invented accuracy or performance
figure.
"""

from __future__ import annotations

from biosense.domain.entities.molecular_characterization import MolecularCharacterizationResult
from biosense.domain.entities.molecular_recognition import RecognitionRecommendation
from biosense.domain.entities.priority_score import BiomarkerPriorityScore
from biosense.domain.entities.rd_scoring import RdCompositeScore, RdScoreFactor
from biosense.domain.entities.sensor_transduction import SensorTransductionCandidate

# INITIAL HEURISTIC WEIGHTS — NOT EMPIRICALLY VALIDATED. These six weights
# were chosen by even-handed judgment (molecular/recognition/sensor feasibility
# weighted equally and highest, since a failure in any one blocks the R&D
# path; evidence and clinical relevance weighted next; data confidence lowest
# since it is a meta-factor about the other five) — not fit to outcome data.
# Recalibrating them against real R&D outcomes is out of scope for Phase 1/1.5
# and is explicitly deferred to a later phase.
#
# Six factors, each documented below (definition / input data / calculation /
# normalization / evidence source):
#
# molecular_fit — definition: how well real molecular-characterization data
#   supports this biomarker as a target. input: MolecularCharacterizationResult
#   (molecular_characteristics list, ctDNA detectability). calculation: 40 pts
#   per characteristic found + 30 pts if ctDNA-detectable. normalization:
#   capped at 100. evidence source: NCI GDC gene/mutation records + linked
#   literature (see MolecularCharacterizationService).
#
# recognition_feasibility — definition: compatibility of the best-scored
#   recognition strategy (DNA hybridization / CRISPR-Cas) with this biomarker.
#   input: RecognitionRecommendation.compatibility_score. calculation: passed
#   through unchanged from the recognition engine (curated domain-graph match
#   score, or its transparent evidence-only heuristic — see
#   MolecularRecognitionEngine). normalization: already 0-100. evidence
#   source: biomarker_recognition_matches domain graph, or molecular
#   characterization evidence when no curated row exists.
#
# sensor_feasibility — definition: feasibility of the best-scored sensor
#   transduction candidate (electrochemical only, Phase 1). input:
#   SensorTransductionCandidate.feasibility_score. calculation: passed through
#   unchanged (0.6 * domain-graph recognition-sensor efficiency + 0.4 *
#   upstream recognition compatibility, see SensorTransductionEngine).
#   normalization: already 0-100. evidence source:
#   recognition_sensor_uses / sensor_performances domain graph tables.
#
# published_evidence — definition: breadth of real, linked citations for this
#   biomarker. input: MolecularCharacterizationResult.evidence (EvidenceRef
#   list). calculation: 25 pts per linked evidence record. normalization:
#   capped at 100. evidence source: PubMed/NCI GDC records linked to the
#   Biomarker row in Postgres.
#
# clinical_relevance — definition: existing clinical-evidence strength for
#   this biomarker, reused rather than recomputed. input:
#   BiomarkerPriorityScore.clinical_evidence component. calculation: passed
#   through unchanged. normalization: already 0-100 (BiomarkerPriorityScore's
#   own scale). evidence source: same as BiomarkerPriorityScore
#   (domain/entities/priority_score.py).
#
# data_confidence — definition: existing data-confidence strength for this
#   biomarker, reused rather than recomputed. input:
#   BiomarkerPriorityScore.data_confidence component. calculation/
#   normalization/evidence source: same as clinical_relevance above.
_WEIGHTS: dict[str, float] = {
    "molecular_fit": 0.20,
    "recognition_feasibility": 0.20,
    "sensor_feasibility": 0.20,
    "published_evidence": 0.15,
    "clinical_relevance": 0.15,
    "data_confidence": 0.10,
}


class RdScoringService:
    def score(
        self,
        *,
        biomarker_name: str,
        characterization: MolecularCharacterizationResult,
        recognition: RecognitionRecommendation | None,
        sensor: SensorTransductionCandidate | None,
        priority_score: BiomarkerPriorityScore | None,
    ) -> RdCompositeScore:
        molecular_fit = self._molecular_fit_factor(characterization)
        recognition_feasibility = self._recognition_factor(recognition)
        sensor_feasibility = self._sensor_factor(sensor)
        published_evidence = self._evidence_factor(characterization)
        clinical_relevance = self._clinical_relevance_factor(priority_score)
        data_confidence = self._data_confidence_factor(priority_score)

        factors = {
            "molecular_fit": molecular_fit,
            "recognition_feasibility": recognition_feasibility,
            "sensor_feasibility": sensor_feasibility,
            "published_evidence": published_evidence,
            "clinical_relevance": clinical_relevance,
            "data_confidence": data_confidence,
        }
        total = round(sum(factors[name].score * weight for name, weight in _WEIGHTS.items()), 2)

        return RdCompositeScore(
            biomarker_name=biomarker_name,
            molecular_fit=molecular_fit,
            recognition_feasibility=recognition_feasibility,
            sensor_feasibility=sensor_feasibility,
            published_evidence=published_evidence,
            clinical_relevance=clinical_relevance,
            data_confidence=data_confidence,
            weights=dict(_WEIGHTS),
            total_score=total,
        )

    def _molecular_fit_factor(self, c: MolecularCharacterizationResult) -> RdScoreFactor:
        if not c.molecular_characteristics:
            return RdScoreFactor(score=0.0, basis="Insufficient evidence: no molecular characteristics derived.", missing_data=True)
        detectable = c.detectability.is_detectable_in_ctdna if c.detectability else None
        score = min(100.0, 40.0 * len(c.molecular_characteristics) + (30.0 if detectable else 0.0))
        return RdScoreFactor(
            score=round(score, 2),
            basis=(
                f"40 pts per molecular characteristic ({len(c.molecular_characteristics)} found) "
                f"+ 30 pts if ctDNA-detectable ({detectable}), capped at 100."
            ),
        )

    def _recognition_factor(self, r: RecognitionRecommendation | None) -> RdScoreFactor:
        if r is None or r.status != "scored" or r.compatibility_score is None:
            return RdScoreFactor(score=0.0, basis="Insufficient evidence: no scored recognition strategy.", missing_data=True)
        return RdScoreFactor(
            score=r.compatibility_score,
            basis=f"Recognition compatibility_score from {r.strategy.value} ({r.status}).",
        )

    def _sensor_factor(self, s: SensorTransductionCandidate | None) -> RdScoreFactor:
        if s is None or s.status != "scored" or s.feasibility_score is None:
            return RdScoreFactor(score=0.0, basis="Insufficient evidence: no scored sensor candidate.", missing_data=True)
        return RdScoreFactor(
            score=s.feasibility_score,
            basis=f"Sensor feasibility_score for {s.platform.value} platform ({s.sensor_name}).",
        )

    def _evidence_factor(self, c: MolecularCharacterizationResult) -> RdScoreFactor:
        n = len(c.evidence)
        if n == 0:
            return RdScoreFactor(score=0.0, basis="Insufficient evidence: no linked citations.", missing_data=True)
        score = min(100.0, 25.0 * n)
        return RdScoreFactor(score=round(score, 2), basis=f"25 pts per linked evidence record ({n} found), capped at 100.")

    def _clinical_relevance_factor(self, p: BiomarkerPriorityScore | None) -> RdScoreFactor:
        if p is None:
            return RdScoreFactor(score=0.0, basis="Insufficient evidence: no BiomarkerPriorityScore available.", missing_data=True)
        c = p.clinical_evidence
        return RdScoreFactor(
            score=c.score,
            basis=f"clinical_evidence component of BiomarkerPriorityScore (source: {c.source}).",
            missing_data=c.missing_data,
        )

    def _data_confidence_factor(self, p: BiomarkerPriorityScore | None) -> RdScoreFactor:
        if p is None:
            return RdScoreFactor(score=0.0, basis="Insufficient evidence: no BiomarkerPriorityScore available.", missing_data=True)
        c = p.data_confidence
        return RdScoreFactor(
            score=c.score,
            basis=f"data_confidence component of BiomarkerPriorityScore (source: {c.source}).",
            missing_data=c.missing_data,
        )
