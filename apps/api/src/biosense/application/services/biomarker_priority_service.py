"""Gather real evidence (Postgres domain graph + live GDC) and score biomarkers.

This is the I/O-bound half of the Biomarker Priority Score: it builds each
ScoreComponent from an actual data source (never a guess), then hands them to the
pure BiomarkerPriorityScorer for weighting. See §12 of the platform upgrade brief:
score + evidence + source + confidence + missing-data must always travel together.
"""

from __future__ import annotations

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from biosense.domain.entities.priority_score import BiomarkerPriorityScore, ScoreComponent
from biosense.domain.services.biomarker_priority_scorer import (
    BiomarkerPriorityScorer,
    count_to_score,
    fraction_to_score,
    rate_to_score,
)
from biosense.domain.services.normalization import normalize_cancer_type
from biosense.infrastructure.external.gdc_client import GdcClient
from biosense.infrastructure.persistence.postgres.models import (
    Biomarker,
    BiomarkerRecognitionMatch,
    Cancer,
    CancerBiomarker,
    PublicHealthFeature,
    RecognitionSensorUse,
)

logger = structlog.get_logger()

# Normalization caps — documented heuristic scales, not clinical thresholds.
_INCIDENCE_RATE_CAP = 100.0  # per 100k; scores saturate at this rate
_PAPER_COUNT_SATURATION = 10
_MUTATION_COUNT_SATURATION = 500


class BiomarkerPriorityService:
    def __init__(self, session: AsyncSession, *, gdc: GdcClient | None = None) -> None:
        self._session = session
        self._gdc = gdc or GdcClient()
        self._scorer = BiomarkerPriorityScorer()

    async def score_biomarkers_for_cancer(self, cancer_type: str) -> list[BiomarkerPriorityScore]:
        code = normalize_cancer_type(cancer_type)
        cancer = (
            await self._session.execute(select(Cancer).where(Cancer.code == code))
        ).scalar_one_or_none()
        if cancer is None:
            return []

        biomarkers = (
            (
                await self._session.execute(
                    select(Biomarker)
                    .join(CancerBiomarker, CancerBiomarker.biomarker_id == Biomarker.id)
                    .where(CancerBiomarker.cancer_id == cancer.id)
                    .options(
                        selectinload(Biomarker.recognition_matches),
                        selectinload(Biomarker.papers),
                    )
                )
            )
            .scalars()
            .unique()
            .all()
        )

        scores = []
        for biomarker in biomarkers:
            scores.append(await self._score_one(biomarker, cancer))
        scores.sort(key=lambda s: s.total_score, reverse=True)
        return scores

    async def score_biomarker(
        self, biomarker_name: str, cancer_type: str
    ) -> BiomarkerPriorityScore | None:
        code = normalize_cancer_type(cancer_type)
        cancer = (
            await self._session.execute(select(Cancer).where(Cancer.code == code))
        ).scalar_one_or_none()
        if cancer is None:
            return None

        biomarker = (
            (
                await self._session.execute(
                    select(Biomarker)
                    .where(Biomarker.name == biomarker_name)
                    .options(
                        selectinload(Biomarker.recognition_matches),
                        selectinload(Biomarker.papers),
                    )
                )
            )
            .scalars()
            .unique()
            .one_or_none()
        )
        if biomarker is None:
            return None

        return await self._score_one(biomarker, cancer)

    async def _score_one(self, biomarker: Biomarker, cancer: Cancer) -> BiomarkerPriorityScore:
        disease_burden = await self._disease_burden(cancer)
        molecular_evidence = await self._molecular_evidence(biomarker)
        clinical_evidence = self._clinical_evidence(biomarker)
        detection_feasibility = self._detection_feasibility(biomarker)
        sensor_compatibility = await self._sensor_compatibility(biomarker)
        data_confidence = self._data_confidence(
            [
                disease_burden,
                molecular_evidence,
                clinical_evidence,
                detection_feasibility,
                sensor_compatibility,
            ]
        )

        return self._scorer.build(
            biomarker_name=biomarker.name,
            cancer_type=cancer.code,
            disease_burden=disease_burden,
            molecular_evidence=molecular_evidence,
            clinical_evidence=clinical_evidence,
            detection_feasibility=detection_feasibility,
            sensor_compatibility=sensor_compatibility,
            data_confidence=data_confidence,
        )

    async def _disease_burden(self, cancer: Cancer) -> ScoreComponent:
        avg_incidence = await self._session.scalar(
            select(func.avg(PublicHealthFeature.value)).where(
                PublicHealthFeature.cancer_id == cancer.id,
                PublicHealthFeature.feature_type == "incidence",
            )
        )
        rate = float(avg_incidence) if avg_incidence is not None else None
        score, missing = rate_to_score(rate, cap=_INCIDENCE_RATE_CAP)
        if missing:
            return ScoreComponent(
                score=0.0,
                evidence=f"No incidence data found for {cancer.code}",
                source="none",
                confidence=0.0,
                missing_data=True,
            )
        return ScoreComponent(
            score=score,
            evidence=f"National average incidence {rate:.1f} per 100k (KOSIS/KDCA)",
            source="KOSIS/KDCA",
            confidence=0.7,
        )

    async def _molecular_evidence(self, biomarker: Biomarker) -> ScoreComponent:
        if not biomarker.gene_symbol:
            return ScoreComponent(
                score=0.0,
                evidence="Biomarker has no associated gene symbol",
                source="none",
                confidence=0.0,
                missing_data=True,
            )
        count = await self._gdc.count_mutations_for_gene(biomarker.gene_symbol)
        score, missing = count_to_score(count, saturating_at=_MUTATION_COUNT_SATURATION)
        if missing:
            return ScoreComponent(
                score=0.0,
                evidence=f"GDC lookup for {biomarker.gene_symbol} failed or returned no data",
                source="NCI GDC",
                confidence=0.0,
                missing_data=True,
            )
        return ScoreComponent(
            score=score,
            evidence=f"{count} recorded somatic mutations for {biomarker.gene_symbol} in GDC",
            source="NCI GDC",
            confidence=0.9,
        )

    def _clinical_evidence(self, biomarker: Biomarker) -> ScoreComponent:
        count = len(biomarker.papers)
        score, _ = count_to_score(count, saturating_at=_PAPER_COUNT_SATURATION)
        if count == 0:
            return ScoreComponent(
                score=0.0,
                evidence="No linked publications found",
                source="none",
                confidence=0.0,
                missing_data=True,
            )
        return ScoreComponent(
            score=score,
            evidence=f"{count} linked publication(s) (PubMed/Europe PMC)",
            source="PubMed/Europe PMC",
            confidence=min(0.5 + count * 0.05, 0.9),
        )

    def _detection_feasibility(self, biomarker: Biomarker) -> ScoreComponent:
        matches: list[BiomarkerRecognitionMatch] = biomarker.recognition_matches
        if not matches:
            return ScoreComponent(
                score=0.0,
                evidence="No recognition-strategy match recorded for this biomarker",
                source="none",
                confidence=0.0,
                missing_data=True,
            )
        best = max(float(m.match_score) for m in matches)
        score, _ = fraction_to_score(best)
        return ScoreComponent(
            score=score,
            evidence=f"Best recognition match score {best:.2f} across {len(matches)} strategy(ies)",
            source="internal domain graph",
            confidence=0.75,
        )

    async def _sensor_compatibility(self, biomarker: Biomarker) -> ScoreComponent:
        matches: list[BiomarkerRecognitionMatch] = biomarker.recognition_matches
        if not matches:
            return ScoreComponent(
                score=0.0,
                evidence="No recognition strategy to look up sensor compatibility",
                source="none",
                confidence=0.0,
                missing_data=True,
            )
        rec_ids = [m.recognition_strategy_id for m in matches]
        result = await self._session.execute(
            select(RecognitionSensorUse.efficiency).where(
                RecognitionSensorUse.recognition_strategy_id.in_(rec_ids)
            )
        )
        efficiencies = [float(e) for (e,) in result.all() if e is not None]
        if not efficiencies:
            return ScoreComponent(
                score=0.0,
                evidence="No sensor implements this biomarker's recognition strategy",
                source="none",
                confidence=0.0,
                missing_data=True,
            )
        best = max(efficiencies)
        score, _ = fraction_to_score(best)
        return ScoreComponent(
            score=score,
            evidence=f"Best sensor efficiency {best:.2f} across {len(efficiencies)} sensor(s)",
            source="internal domain graph",
            confidence=0.7,
        )

    def _data_confidence(self, components: list[ScoreComponent]) -> ScoreComponent:
        present = sum(1 for c in components if not c.missing_data)
        total = len(components)
        score = round(present / total * 100.0, 2)
        return ScoreComponent(
            score=score,
            evidence=f"{present} of {total} evidence factors backed by real data",
            source="internal (derived)",
            confidence=1.0,
            missing_data=False,
        )
