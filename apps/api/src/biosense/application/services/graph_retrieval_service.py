import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from biosense.domain.entities.recommendation import ExtractedFeatures, GraphCandidate
from biosense.infrastructure.persistence.postgres.models import (
    Biomarker,
    BiomarkerRecognitionMatch,
    Cancer,
    CtDNA,
    Protocol,
    PublicHealthFeature,
    RecognitionSensorUse,
    RecognitionStrategy,
    Sensor,
    SensorPerformance,
    CancerBiomarker,
)

logger = structlog.get_logger()


class GraphRetrievalService:
    """Traverse Cancer → Biomarker → Recognition → Sensor graph in Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def retrieve_candidates(
        self, features: ExtractedFeatures, limit: int = 20
    ) -> list[GraphCandidate]:
        cancer_id = await self._session.scalar(
            select(Cancer.id).where(Cancer.code == features.cancer_type)
        )
        if not cancer_id:
            logger.warning("cancer_not_found", cancer_type=features.cancer_type)
            return []

        ctdna_id = await self._session.scalar(
            select(CtDNA.id).where(CtDNA.code == features.ctdna_class)
        )

        biomarker_query = (
            select(Biomarker)
            .join(CancerBiomarker, CancerBiomarker.biomarker_id == Biomarker.id)
            .where(CancerBiomarker.cancer_id == cancer_id)
            .options(
                selectinload(Biomarker.recognition_matches).selectinload(
                    BiomarkerRecognitionMatch.recognition_strategy
                ),
            )
        )
        if ctdna_id:
            biomarker_query = biomarker_query.where(Biomarker.ctdna_id == ctdna_id)

        result = await self._session.execute(biomarker_query)
        biomarkers = list(result.scalars().unique().all())

        if features.biomarker_hints:
            hints = {h.lower() for h in features.biomarker_hints}
            biomarkers = [b for b in biomarkers if any(h in b.name.lower() for h in hints)] or biomarkers

        candidates: list[GraphCandidate] = []
        for biomarker in biomarkers:
            paths = await self._expand_biomarker_paths(biomarker)
            candidates.extend(paths)

        candidates.sort(key=lambda c: c.match_score * c.sensor_efficiency, reverse=True)
        logger.info("graph_retrieval_complete", candidates=len(candidates[:limit]))
        return candidates[:limit]

    async def _expand_biomarker_paths(self, biomarker: Biomarker) -> list[GraphCandidate]:
        if not biomarker.recognition_matches:
            return []

        rec_ids = [m.recognition_strategy_id for m in biomarker.recognition_matches]
        match_map = {m.recognition_strategy_id: m for m in biomarker.recognition_matches}

        uses_result = await self._session.execute(
            select(RecognitionSensorUse, RecognitionStrategy, Sensor)
            .join(RecognitionStrategy, RecognitionStrategy.id == RecognitionSensorUse.recognition_strategy_id)
            .join(Sensor, Sensor.id == RecognitionSensorUse.sensor_id)
            .where(RecognitionSensorUse.recognition_strategy_id.in_(rec_ids))
        )

        candidates: list[GraphCandidate] = []
        for use, recognition, sensor in uses_result.all():
            match = match_map[recognition.id]
            perf = await self._best_performance(sensor.id)
            protocol = await self._best_protocol(sensor.id)

            path = (
                f"Cancer→{biomarker.name}→{recognition.code}→{sensor.sensor_type}"
            )
            candidates.append(
                GraphCandidate(
                    biomarker_id=str(biomarker.id),
                    biomarker_name=biomarker.name,
                    recognition_id=str(recognition.id),
                    recognition_code=recognition.code,
                    recognition_name=recognition.name,
                    sensor_id=str(sensor.id),
                    sensor_name=sensor.name,
                    sensor_type=sensor.sensor_type,
                    match_score=float(match.match_score),
                    sensor_efficiency=float(use.efficiency or 0.7),
                    sensitivity=float(perf.sensitivity) if perf and perf.sensitivity else None,
                    specificity=float(perf.specificity) if perf and perf.specificity else None,
                    lod_value=float(perf.lod_value) if perf and perf.lod_value else None,
                    lod_unit=perf.lod_unit if perf else None,
                    estimated_cost_usd=float(sensor.estimated_cost_usd)
                    if sensor.estimated_cost_usd
                    else None,
                    protocol_steps=protocol.steps if protocol else [],
                    graph_path=path,
                )
            )
        return candidates

    async def _best_performance(self, sensor_id) -> SensorPerformance | None:
        result = await self._session.execute(
            select(SensorPerformance)
            .where(SensorPerformance.sensor_id == sensor_id)
            .order_by(SensorPerformance.sensitivity.desc().nulls_last())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _best_protocol(self, sensor_id) -> Protocol | None:
        result = await self._session.execute(
            select(Protocol).where(Protocol.sensor_id == sensor_id).limit(1)
        )
        return result.scalar_one_or_none()


class PublicHealthFeatureService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def fetch_features(
        self, cancer_type: str, region_code: str
    ) -> tuple[float | None, float | None, float]:
        cancer_id = await self._session.scalar(
            select(Cancer.id).where(Cancer.code == cancer_type)
        )
        if not cancer_id:
            return None, None, 0.5

        result = await self._session.execute(
            select(PublicHealthFeature).where(
                PublicHealthFeature.cancer_id == cancer_id,
                PublicHealthFeature.region_code == region_code,
            )
        )
        features = list(result.scalars().all())
        incidence = next((f for f in features if f.feature_type == "incidence"), None)
        mortality = next((f for f in features if f.feature_type == "mortality"), None)

        inc_val = float(incidence.value) if incidence else None
        mort_val = float(mortality.value) if mortality else None
        score = _public_health_score(inc_val, mort_val)
        return inc_val, mort_val, score


def _public_health_score(incidence: float | None, mortality: float | None) -> float:
    if incidence is None and mortality is None:
        return 0.5
    raw = (incidence or 0) / 100.0 + (mortality or 0) / 100.0
    return round(min(max(raw, 0.0), 1.0), 4)
