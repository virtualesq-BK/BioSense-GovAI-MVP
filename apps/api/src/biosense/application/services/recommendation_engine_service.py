import json
import time
import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.application.services.feature_extraction_service import FeatureExtractionService
from biosense.application.services.graph_retrieval_service import (
    GraphRetrievalService,
    PublicHealthFeatureService,
)
from biosense.application.services.hybrid_retrieval_service import HybridRetrievalService
from biosense.config import settings
from biosense.domain.entities.recommendation import (
    ExpectedMetrics,
    RecommendationInput,
    SensorRecommendation,
)
from biosense.infrastructure.ai.openai_client import create_openai_client
from biosense.infrastructure.persistence.postgres.models import Recommendation

logger = structlog.get_logger()

LLM_REFINE_SYSTEM = """You refine biosensor recommendations for ctDNA cancer detection.
Given ranked candidates and context, output JSON with a short rationale per recommendation.
Respond with: {"rationales": ["...", "..."]}"""


class RecommendationEngineService:
    """
    Biomarker–sensor recommendation engine.

    Pipeline: Feature Extraction → Graph Retrieval → Hybrid Ranking → LLM Rationale
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._features = FeatureExtractionService()
        self._public_health = PublicHealthFeatureService(session)
        self._graph = GraphRetrievalService(session)
        self._hybrid = HybridRetrievalService(session)
        self._client = create_openai_client()

    async def generate(
        self,
        inp: RecommendationInput,
        *,
        top_k: int = 3,
        persist: bool = False,
        biomarker_case_id: uuid.UUID | None = None,
    ) -> list[SensorRecommendation]:
        start = time.perf_counter()

        ph = await self._public_health.fetch_features(inp.cancer_type, inp.region_code)
        features = self._features.extract(inp, public_health=ph)

        graph_candidates = await self._graph.retrieve_candidates(features)
        ranked = await self._hybrid.retrieve_and_rank(features, graph_candidates, top_k=top_k)

        if not ranked:
            logger.warning("no_candidates_found", cancer=inp.cancer_type)
            return []

        rationales = await self._llm_rationales(inp, ranked)

        recommendations: list[SensorRecommendation] = []
        for i, scored in enumerate(ranked, start=1):
            c = scored.candidate
            rationale = rationales[i - 1] if i - 1 < len(rationales) else _default_rationale(c)

            metrics = ExpectedMetrics(
                sensitivity=c.sensitivity or 0.85,
                specificity=c.specificity or 0.90,
                lod_value=c.lod_value or 0.5,
                lod_unit=c.lod_unit or "ng/mL",
                estimated_cost_usd=c.estimated_cost_usd or 50.0,
            )

            protocol = {
                "steps": c.protocol_steps
                or [
                    "Prepare sample",
                    "Immobilize recognition element",
                    "Incubate with ctDNA target",
                    "Measure signal",
                ],
                "reagents": [c.recognition_name, "buffer", "wash solution"],
                "duration_hours": 6.0,
            }

            cites = scored.literature_citations
            literature_ids: list[str] = []
            seen_ids: set[str] = set()
            for cit in cites:
                pid = cit.get("paper_id") or cit.get("paper_external_id")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    literature_ids.append(str(pid))

            public_health_evidence: dict = {
                "incidence_rate": ph.incidence_rate,
                "mortality_rate": ph.mortality_rate,
                "region_code": ph.region_code or inp.region_code,
                "national_incidence_avg": ph.national_incidence_avg,
                "national_mortality_avg": ph.national_mortality_avg,
            }
            if features.public_health_narrative:
                public_health_evidence["narrative"] = features.public_health_narrative

            evidence = {
                "literature_ids": literature_ids,
                "citations": cites,
                "graph_paths": [c.graph_path],
                "public_health": public_health_evidence,
            }

            recommendations.append(
                SensorRecommendation(
                    rank=i,
                    sensor_type=c.sensor_type,
                    sensor_name=c.sensor_name,
                    recognition_strategy=c.recognition_code,
                    recognition_name=c.recognition_name,
                    biomarker_name=c.biomarker_name,
                    expected_metrics=metrics,
                    experimental_protocol=protocol,
                    confidence_score=scored.confidence,
                    composite_score=scored.composite_score,
                    rationale=rationale,
                    evidence=evidence,
                )
            )

        if persist and biomarker_case_id:
            await self._persist_recommendations(biomarker_case_id, recommendations)

        elapsed = int((time.perf_counter() - start) * 1000)
        logger.info(
            "recommendation_engine_complete",
            count=len(recommendations),
            latency_ms=elapsed,
        )
        return recommendations

    async def _llm_rationales(self, inp: RecommendationInput, ranked: list) -> list[str]:
        if not self._client:
            return [_default_rationale(s.candidate) for s in ranked]

        summary = "\n".join(
            f"{i}. {s.candidate.sensor_type}/{s.candidate.recognition_code} "
            f"score={s.composite_score} biomarker={s.candidate.biomarker_name}"
            for i, s in enumerate(ranked, 1)
        )
        prompt = f"""Case: {inp.cancer_type} cancer, ctDNA class {inp.ctdna_class},
region {inp.region_code}, age {inp.patient_age}.

Ranked candidates:
{summary}

Provide one rationale sentence per candidate."""

        try:
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": LLM_REFINE_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)
            rationales = data.get("rationales", [])
            if rationales:
                return rationales
        except Exception as exc:
            logger.warning("llm_rationale_failed", error=str(exc))

        return [_default_rationale(s.candidate) for s in ranked]

    async def _persist_recommendations(
        self, case_id: uuid.UUID, recs: list[SensorRecommendation]
    ) -> None:
        for rec in recs:
            m = rec.expected_metrics
            self._session.add(
                Recommendation(
                    biomarker_case_id=case_id,
                    rank=rec.rank,
                    sensor_type=rec.sensor_type,
                    recognition_strategy=rec.recognition_strategy,
                    sensor_id=uuid.UUID(rec.evidence.get("sensor_id"))
                    if rec.evidence.get("sensor_id")
                    else None,
                    expected_sensitivity=m.sensitivity,
                    expected_specificity=m.specificity,
                    expected_lod_value=m.lod_value,
                    expected_lod_unit=m.lod_unit,
                    estimated_cost_usd=m.estimated_cost_usd,
                    experimental_protocol=rec.experimental_protocol,
                    confidence_score=rec.confidence_score,
                    evidence=rec.evidence,
                )
            )
        await self._session.flush()


def _default_rationale(candidate) -> str:
    return (
        f"Graph path {candidate.graph_path} supports {candidate.recognition_name} "
        f"on {candidate.sensor_name} for {candidate.biomarker_name} detection."
    )
