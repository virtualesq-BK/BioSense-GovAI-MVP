import json
import time
from dataclasses import asdict

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.config import settings
from biosense.domain.entities.literature import BiomarkerRecommendation, Citation, RetrievedChunk
from biosense.infrastructure.ai.embedding_service import EmbeddingService
from biosense.infrastructure.ai.openai_client import create_openai_client
from biosense.infrastructure.persistence.postgres.literature_repository import LiteratureRepository

logger = structlog.get_logger()

BIOMARKER_RAG_SYSTEM = """You are a biomedical expert specializing in ctDNA biomarkers and biosensor design.
Given retrieved scientific literature passages, produce biomarker-based biosensor recommendations.
Always cite evidence from the provided passages. Output valid JSON only."""


class LiteratureRetrievalService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = LiteratureRepository(session)
        self._embedder = EmbeddingService()

    async def retrieve(
        self, query: str, top_k: int | None = None
    ) -> list[RetrievedChunk]:
        k = top_k or settings.literature_rag_top_k
        embedding = await self._embedder.embed_text(query)
        chunks = await self._repo.similarity_search(embedding, top_k=k)
        logger.info("retrieval_complete", query=query[:80], results=len(chunks))
        return chunks


class LiteratureRagQueryService:
    """RAG query → biomarker recommendations with citations."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = LiteratureRepository(session)
        self._retrieval = LiteratureRetrievalService(session)
        self._client = create_openai_client()

    async def query(
        self,
        query_text: str,
        *,
        cancer_type: str | None = None,
        biomarker_name: str | None = None,
        top_k: int | None = None,
    ) -> dict:
        start = time.perf_counter()
        k = top_k or settings.literature_rag_top_k

        context_query = query_text
        if biomarker_name:
            context_query += f" biomarker: {biomarker_name}"
        if cancer_type:
            context_query += f" cancer: {cancer_type}"

        chunks = await self._retrieval.retrieve(context_query, top_k=k)
        citations = [_chunk_to_citation(c) for c in chunks]
        recommendations = await self._generate_recommendations(
            query_text, cancer_type, biomarker_name, chunks
        )

        latency_ms = int((time.perf_counter() - start) * 1000)
        rec_dicts = [_recommendation_to_dict(r) for r in recommendations]
        cit_dicts = [_citation_to_dict(c) for c in citations]

        await self._repo.log_query(
            query_text=query_text,
            cancer_type=cancer_type,
            biomarker_name=biomarker_name,
            top_k=k,
            chunks_retrieved=len(chunks),
            recommendations=rec_dicts,
            citations=cit_dicts,
            latency_ms=latency_ms,
        )

        return {
            "query": query_text,
            "cancer_type": cancer_type,
            "biomarker_name": biomarker_name,
            "recommendations": rec_dicts,
            "citations": cit_dicts,
            "chunks_retrieved": len(chunks),
            "latency_ms": latency_ms,
        }

    async def _generate_recommendations(
        self,
        query: str,
        cancer_type: str | None,
        biomarker_name: str | None,
        chunks: list[RetrievedChunk],
    ) -> list[BiomarkerRecommendation]:
        if not chunks:
            return []

        if self._client is None:
            return _fallback_recommendations(query, biomarker_name, chunks)

        context = "\n\n---\n\n".join(
            f"[{c.paper_external_id} chunk {c.chunk_index}] {c.content[:600]}"
            for c in chunks
        )
        user_prompt = f"""Query: {query}
Cancer type: {cancer_type or 'unspecified'}
Biomarker focus: {biomarker_name or 'unspecified'}

Literature passages:
{context}

Return JSON array of 1-3 biomarker recommendations:
[{{"biomarker_name": "...", "sensor_strategy": "...", "recognition_approach": "...",
   "rationale": "...", "confidence": 0.0-1.0, "cited_paper_ids": ["pmid:..."]}}]"""

        response = await self._client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": BIOMARKER_RAG_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw = response.choices[0].message.content or "{}"
        return _parse_llm_recommendations(raw, chunks)


class LiteratureEvaluationService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = LiteratureRepository(session)
        self._retrieval = LiteratureRetrievalService(session)

    async def evaluate(
        self,
        query_text: str,
        expected_terms: list[str],
        top_k: int = 5,
    ) -> dict:
        chunks = await self._retrieval.retrieve(query_text, top_k=top_k)
        if not chunks:
            result = {
                "precision_at_k": 0.0,
                "recall_at_k": 0.0,
                "citation_coverage": 0.0,
                "mrr": 0.0,
                "chunks_evaluated": 0,
            }
        else:
            result = _compute_metrics(chunks, expected_terms, top_k)

        ev = await self._repo.save_evaluation(
            query_text=query_text,
            precision_at_k=result["precision_at_k"],
            recall_at_k=result["recall_at_k"],
            citation_coverage=result["citation_coverage"],
            mrr=result["mrr"],
            chunks_evaluated=result["chunks_evaluated"],
            details={"expected_terms": expected_terms, "top_k": top_k},
        )
        return {
            "evaluation_id": str(ev.id),
            **result,
            "expected_terms": expected_terms,
        }


def _chunk_to_citation(chunk: RetrievedChunk) -> Citation:
    return Citation(
        paper_external_id=chunk.paper_external_id,
        paper_title=chunk.paper_title,
        chunk_id=chunk.chunk_id,
        excerpt=chunk.content[:300],
        relevance_score=chunk.score,
    )


def _citation_to_dict(c: Citation) -> dict:
    return asdict(c)


def _recommendation_to_dict(r: BiomarkerRecommendation) -> dict:
    d = asdict(r)
    d["citations"] = [asdict(c) for c in r.citations]
    return d


def _fallback_recommendations(
    query: str,
    biomarker_name: str | None,
    chunks: list[RetrievedChunk],
) -> list[BiomarkerRecommendation]:
    name = biomarker_name or "ctDNA biomarker"
    citations = [_chunk_to_citation(chunks[0])] if chunks else []
    return [
        BiomarkerRecommendation(
            biomarker_name=name,
            sensor_strategy="electrochemical",
            recognition_approach="aptamer-based",
            rationale=f"Literature-supported approach for: {query[:120]}",
            confidence=round(chunks[0].score, 3) if chunks else 0.5,
            citations=citations,
        )
    ]


def _parse_llm_recommendations(
    raw: str, chunks: list[RetrievedChunk]
) -> list[BiomarkerRecommendation]:
    try:
        data = json.loads(raw)
        items = data if isinstance(data, list) else data.get("recommendations", data.get("items", []))
    except json.JSONDecodeError:
        return _fallback_recommendations("", None, chunks)

    chunk_map = {c.paper_external_id: c for c in chunks}
    results: list[BiomarkerRecommendation] = []
    for item in items[:3]:
        cited_ids = item.get("cited_paper_ids", [])
        citations = [
            _chunk_to_citation(chunk_map[pid])
            for pid in cited_ids
            if pid in chunk_map
        ]
        if not citations and chunks:
            citations = [_chunk_to_citation(chunks[0])]

        results.append(
            BiomarkerRecommendation(
                biomarker_name=item.get("biomarker_name", "unknown"),
                sensor_strategy=item.get("sensor_strategy", "electrochemical"),
                recognition_approach=item.get("recognition_approach", "aptamer-based"),
                rationale=item.get("rationale", ""),
                confidence=float(item.get("confidence", 0.7)),
                citations=citations,
            )
        )
    return results


def _compute_metrics(
    chunks: list[RetrievedChunk], expected_terms: list[str], top_k: int
) -> dict:
    terms_lower = [t.lower() for t in expected_terms]
    relevant_positions: list[int] = []
    for i, chunk in enumerate(chunks):
        content_lower = chunk.content.lower()
        if any(term in content_lower for term in terms_lower):
            relevant_positions.append(i)

    hits = len(relevant_positions)
    precision = hits / len(chunks) if chunks else 0.0
    recall = hits / len(expected_terms) if expected_terms else 0.0
    mrr = 0.0
    if relevant_positions:
        mrr = 1.0 / (relevant_positions[0] + 1)

    unique_papers = {c.paper_external_id for c in chunks}
    cited_papers = {
        c.paper_external_id
        for c in chunks
        if any(t in c.content.lower() for t in terms_lower)
    }
    citation_coverage = len(cited_papers) / len(unique_papers) if unique_papers else 0.0

    return {
        "precision_at_k": round(precision, 4),
        "recall_at_k": round(min(recall, 1.0), 4),
        "citation_coverage": round(citation_coverage, 4),
        "mrr": round(mrr, 4),
        "chunks_evaluated": len(chunks),
    }
