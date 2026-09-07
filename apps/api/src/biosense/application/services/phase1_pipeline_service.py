"""Orchestrates the Phase 1 Multi-Omics Bio R&D pipeline for one biomarker.

Cancer -> Biomarker Candidate -> Molecular Characterization -> Molecular
Recognition Strategy -> Signal Transduction -> Evidence-backed composite score.

This is the additive Phase 1 extension wired into the existing R&D Design
Report (`RndDesignReportService`) — it does not replace anything there, it
adds the new mutation/ctDNA-dimension sections.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from biosense.application.services.molecular_characterization_service import (
    MolecularCharacterizationService,
)
from biosense.application.services.molecular_detectability_service import (
    MolecularDetectabilityService,
)
from biosense.application.services.molecular_recognition_service import MolecularRecognitionEngine
from biosense.application.services.rd_scoring_service import RdScoringService
from biosense.application.services.sensor_transduction_service import SensorTransductionEngine
from biosense.domain.entities.molecular_characterization import MolecularCharacterizationResult
from biosense.domain.entities.molecular_detectability import MolecularDetectabilityResult
from biosense.domain.entities.molecular_recognition import RecognitionRecommendation
from biosense.domain.entities.priority_score import BiomarkerPriorityScore
from biosense.domain.entities.rd_scoring import RdCompositeScore
from biosense.domain.entities.sensor_transduction import SensorTransductionCandidate
from biosense.infrastructure.external.gdc_client import GdcClient
from biosense.infrastructure.persistence.postgres.models import (
    Biomarker,
    BiomarkerRecognitionMatch,
    RecognitionSensorUse,
    RecognitionStrategy,
    Sensor,
)

_PHASE1_DISCLAIMER = (
    "Phase 1 output covers the mutation/ctDNA biomarker dimension with DNA "
    "hybridization and CRISPR-Cas recognition and electrochemical sensor "
    "transduction only. This is a research-support tool, not a diagnostic "
    "system — no clinical validation or regulatory approval is claimed or "
    "implied, and AI-generated predictions are not a substitute for "
    "experimental (wet-lab) validation."
)


@dataclass(frozen=True)
class Phase1PipelineResult:
    molecular_characterization: MolecularCharacterizationResult | None
    detectability: MolecularDetectabilityResult | None
    recognition_recommendations: list[RecognitionRecommendation]
    sensor_transduction_candidates: list[SensorTransductionCandidate]
    composite_score: RdCompositeScore | None
    disclaimers: list[str]


class Phase1PipelineService:
    def __init__(self, session: AsyncSession, *, gdc: GdcClient | None = None) -> None:
        self._session = session
        self._characterization = MolecularCharacterizationService(gdc=gdc)
        self._detectability = MolecularDetectabilityService()
        self._recognition = MolecularRecognitionEngine()
        self._transduction = SensorTransductionEngine()
        self._scoring = RdScoringService()

    async def run(
        self,
        *,
        biomarker: Biomarker | None,
        cancer_code: str,
        priority_score: BiomarkerPriorityScore | None,
    ) -> Phase1PipelineResult:
        characterization = await self._characterization.characterize(
            biomarker, cancer_code=cancer_code
        )

        detectability = self._detectability.assess(characterization)

        if biomarker is None:
            return Phase1PipelineResult(
                molecular_characterization=characterization,
                detectability=detectability,
                recognition_recommendations=[],
                sensor_transduction_candidates=[],
                composite_score=None,
                disclaimers=[_PHASE1_DISCLAIMER],
            )

        graph_matches = await self._load_recognition_matches(biomarker.id)
        recognition_recommendations = self._recognition.recommend(
            characterization, graph_matches=graph_matches, detectability=detectability
        )
        recognition_recommendations = await self._recognition.attach_crispr_citations(
            recognition_recommendations, gene_symbol=biomarker.gene_symbol
        )
        top_recognition = next(
            (r for r in recognition_recommendations if r.status == "scored"), None
        )

        sensor_candidates: list[SensorTransductionCandidate] = []
        composite_score: RdCompositeScore | None = None
        if top_recognition is not None:
            sensor_uses = await self._load_sensor_uses(top_recognition.strategy.value)
            sensor_candidates = self._transduction.transduce(
                top_recognition, sensor_uses=sensor_uses
            )
            top_sensor = next((s for s in sensor_candidates if s.status == "scored"), None)
            composite_score = self._scoring.score(
                biomarker_name=biomarker.name,
                characterization=characterization,
                recognition=top_recognition,
                sensor=top_sensor,
                priority_score=priority_score,
            )

        return Phase1PipelineResult(
            molecular_characterization=characterization,
            detectability=detectability,
            recognition_recommendations=recognition_recommendations,
            sensor_transduction_candidates=sensor_candidates,
            composite_score=composite_score,
            disclaimers=[_PHASE1_DISCLAIMER],
        )

    async def _load_recognition_matches(self, biomarker_id) -> list[BiomarkerRecognitionMatch]:
        rows = await self._session.execute(
            select(BiomarkerRecognitionMatch)
            .where(BiomarkerRecognitionMatch.biomarker_id == biomarker_id)
            .options(selectinload(BiomarkerRecognitionMatch.recognition_strategy))
        )
        return list(rows.scalars().unique().all())

    async def _load_sensor_uses(self, recognition_code: str) -> list[RecognitionSensorUse]:
        strategy = (
            await self._session.execute(
                select(RecognitionStrategy).where(RecognitionStrategy.code == recognition_code)
            )
        ).scalar_one_or_none()
        if strategy is None:
            return []
        rows = await self._session.execute(
            select(RecognitionSensorUse)
            .where(RecognitionSensorUse.recognition_strategy_id == strategy.id)
            .options(
                selectinload(RecognitionSensorUse.sensor).selectinload(Sensor.performances)
            )
        )
        return list(rows.scalars().unique().all())
