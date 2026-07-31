import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.application.services.literature_rag_service import LiteratureRetrievalService
from biosense.domain.entities.recommendation import ExtractedFeatures, GraphCandidate
from biosense.domain.services.weighted_ranker import WeightedRanker

logger = structlog.get_logger()


class HybridRetrievalService:
    """
    Hybrid retrieval: graph candidates boosted by literature vector similarity.
    Maps literature chunk relevance to sensor/recognition pairs.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._literature = LiteratureRetrievalService(session)
        self._ranker = WeightedRanker()

    async def retrieve_and_rank(
        self,
        features: ExtractedFeatures,
        graph_candidates: list[GraphCandidate],
        *,
        top_k: int = 3,
    ) -> list:
        if not graph_candidates:
            return []

        chunks = await self._literature.retrieve(features.query_text, top_k=8)
        lit_scores, citations = _map_literature_to_candidates(graph_candidates, chunks)

        ranked = self._ranker.rank(
            graph_candidates,
            literature_scores=lit_scores,
            public_health_score=features.public_health_score,
            literature_citations=citations,
        )
        logger.info(
            "hybrid_retrieval_complete",
            graph_candidates=len(graph_candidates),
            literature_chunks=len(chunks),
            top_score=ranked[0].composite_score if ranked else 0,
        )
        return ranked[:top_k]


def _map_literature_to_candidates(
    candidates: list[GraphCandidate], chunks: list
) -> tuple[dict[str, float], dict[str, list[dict]]]:
    scores: dict[str, float] = {}
    citations: dict[str, list[dict]] = {}

    for candidate in candidates:
        key = f"{candidate.sensor_id}:{candidate.recognition_id}"
        best_score = 0.0
        cites: list[dict] = []

        for chunk in chunks:
            content_lower = chunk.content.lower()
            relevance = chunk.score
            keyword_hits = sum(
                1
                for term in [
                    candidate.biomarker_name.lower(),
                    candidate.sensor_type.lower(),
                    candidate.recognition_code.replace("_", " "),
                    candidate.sensor_name.lower(),
                ]
                if term and term in content_lower
            )
            if keyword_hits > 0:
                boosted = min(1.0, relevance + 0.1 * keyword_hits)
                if boosted > best_score:
                    best_score = boosted
                cites.append(
                    {
                        "paper_external_id": chunk.paper_external_id,
                        "paper_title": chunk.paper_title,
                        "chunk_id": chunk.chunk_id,
                        "excerpt": chunk.content[:200],
                        "relevance_score": round(boosted, 4),
                    }
                )

        scores[key] = round(best_score, 4)
        citations[key] = cites[:3]

    return scores, citations
