import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.domain.entities.literature import ExtractedMetric, RetrievedChunk, TextChunk
from biosense.infrastructure.persistence.postgres.models import (
    LiteratureIngestionJob,
    Paper,
    PaperChunk,
    RagEvaluation,
    RagQueryLog,
    Sensor,
    SensorPerformance,
)

logger = structlog.get_logger()


class LiteratureRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_paper(
        self,
        *,
        external_id: str,
        title: str,
        source: str = "upload",
        authors: list[str] | None = None,
        pdf_filename: str | None = None,
        abstract: str | None = None,
        published_at=None,
        metadata: dict | None = None,
    ) -> Paper:
        paper = Paper(
            external_id=external_id,
            title=title,
            source=source,
            authors=authors,
            pdf_filename=pdf_filename,
            abstract=abstract,
            published_at=published_at,
            metadata_=metadata or {},
            ingestion_status="pending",
        )
        self._session.add(paper)
        await self._session.flush()
        return paper

    async def get_paper(self, paper_id: uuid.UUID) -> Paper | None:
        return await self._session.get(Paper, paper_id)

    async def get_paper_by_external_id(self, external_id: str) -> Paper | None:
        result = await self._session.execute(
            select(Paper).where(Paper.external_id == external_id)
        )
        return result.scalar_one_or_none()

    async def list_papers(self, limit: int = 50) -> list[Paper]:
        result = await self._session.execute(
            select(Paper).order_by(Paper.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def create_ingestion_job(self, paper_id: uuid.UUID) -> LiteratureIngestionJob:
        job = LiteratureIngestionJob(paper_id=paper_id, status="pending")
        self._session.add(job)
        await self._session.flush()
        return job

    async def mark_ingestion_running(self, job_id: uuid.UUID) -> None:
        job = await self._session.get(LiteratureIngestionJob, job_id)
        paper = await self._session.get(Paper, job.paper_id) if job else None
        if job:
            job.status = "running"
            job.started_at = datetime.now(UTC)
        if paper:
            paper.ingestion_status = "processing"

    async def complete_ingestion(
        self, job_id: uuid.UUID, paper_id: uuid.UUID, chunks_created: int
    ) -> None:
        job = await self._session.get(LiteratureIngestionJob, job_id)
        paper = await self._session.get(Paper, paper_id)
        if job:
            job.status = "completed"
            job.chunks_created = chunks_created
            job.finished_at = datetime.now(UTC)
        if paper:
            paper.ingestion_status = "indexed"
            paper.chunk_count = chunks_created

    async def fail_ingestion(
        self, job_id: uuid.UUID, paper_id: uuid.UUID, error: str
    ) -> None:
        job = await self._session.get(LiteratureIngestionJob, job_id)
        paper = await self._session.get(Paper, paper_id)
        if job:
            job.status = "failed"
            job.error_message = error
            job.finished_at = datetime.now(UTC)
        if paper:
            paper.ingestion_status = "failed"

    async def replace_chunks(
        self, paper_id: uuid.UUID, chunks: list[TextChunk], embeddings: list[list[float]]
    ) -> int:
        await self._session.execute(delete(PaperChunk).where(PaperChunk.paper_id == paper_id))
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            self._session.add(
                PaperChunk(
                    paper_id=paper_id,
                    chunk_index=chunk.index,
                    content=chunk.content,
                    embedding=embedding,
                    metadata_=chunk.metadata,
                )
            )
        return len(chunks)

    async def similarity_search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[RetrievedChunk]:
        embedding_literal = "[" + ",".join(str(v) for v in query_embedding) + "]"
        sql = text("""
            SELECT
                pc.id AS chunk_id,
                pc.paper_id,
                p.external_id,
                p.title,
                pc.content,
                pc.chunk_index,
                1 - (pc.embedding <=> CAST(:embedding AS vector)) AS score
            FROM paper_chunks pc
            JOIN papers p ON p.id = pc.paper_id
            WHERE pc.embedding IS NOT NULL
              AND p.ingestion_status = 'indexed'
            ORDER BY pc.embedding <=> CAST(:embedding AS vector)
            LIMIT :top_k
        """)
        result = await self._session.execute(
            sql, {"embedding": embedding_literal, "top_k": top_k}
        )
        rows = result.mappings().all()
        return [
            RetrievedChunk(
                chunk_id=str(row["chunk_id"]),
                paper_id=str(row["paper_id"]),
                paper_external_id=row["external_id"],
                paper_title=row["title"],
                content=row["content"],
                score=float(row["score"]),
                chunk_index=int(row["chunk_index"]),
            )
            for row in rows
        ]

    async def log_query(
        self,
        *,
        query_text: str,
        cancer_type: str | None,
        biomarker_name: str | None,
        top_k: int,
        chunks_retrieved: int,
        recommendations: list[dict],
        citations: list[dict],
        latency_ms: int,
    ) -> RagQueryLog:
        log = RagQueryLog(
            query_text=query_text,
            cancer_type=cancer_type,
            biomarker_name=biomarker_name,
            top_k=top_k,
            chunks_retrieved=chunks_retrieved,
            recommendations=recommendations,
            citations=citations,
            latency_ms=latency_ms,
        )
        self._session.add(log)
        await self._session.flush()
        return log

    async def save_evaluation(
        self,
        *,
        query_text: str,
        precision_at_k: float,
        recall_at_k: float,
        citation_coverage: float,
        mrr: float,
        chunks_evaluated: int,
        details: dict,
    ) -> RagEvaluation:
        ev = RagEvaluation(
            query_text=query_text,
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            citation_coverage=citation_coverage,
            mrr=mrr,
            chunks_evaluated=chunks_evaluated,
            details=details,
        )
        self._session.add(ev)
        await self._session.flush()
        return ev

    async def get_ingestion_stats(self) -> dict:
        total = await self._session.scalar(select(func.count()).select_from(Paper))
        indexed = await self._session.scalar(
            select(func.count()).select_from(Paper).where(Paper.ingestion_status == "indexed")
        )
        pending = await self._session.scalar(
            select(func.count()).select_from(Paper).where(Paper.ingestion_status == "pending")
        )
        failed = await self._session.scalar(
            select(func.count()).select_from(Paper).where(Paper.ingestion_status == "failed")
        )
        chunk_total = await self._session.scalar(select(func.count()).select_from(PaperChunk))
        return {
            "total_papers": total or 0,
            "indexed_papers": indexed or 0,
            "pending_papers": pending or 0,
            "failed_papers": failed or 0,
            "total_chunks": chunk_total or 0,
        }

    async def list_evaluations(self, limit: int = 20) -> list[RagEvaluation]:
        result = await self._session.execute(
            select(RagEvaluation).order_by(RagEvaluation.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def list_ingestion_jobs(self, limit: int = 20) -> list[LiteratureIngestionJob]:
        result = await self._session.execute(
            select(LiteratureIngestionJob)
            .order_by(LiteratureIngestionJob.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_paper_chunk_texts(self, paper_id: uuid.UUID) -> list[str]:
        result = await self._session.execute(
            select(PaperChunk.content)
            .where(PaperChunk.paper_id == paper_id)
            .order_by(PaperChunk.chunk_index)
        )
        return [row[0] for row in result.all() if row[0]]

    async def list_sensors(self) -> list[dict]:
        result = await self._session.execute(select(Sensor.id, Sensor.name, Sensor.sensor_type))
        return [
            {"id": row.id, "name": row.name, "sensor_type": row.sensor_type}
            for row in result.all()
        ]

    async def upsert_extracted_performance(
        self,
        *,
        sensor_id: uuid.UUID,
        paper_id: uuid.UUID,
        metric: ExtractedMetric,
    ) -> SensorPerformance:
        result = await self._session.execute(
            select(SensorPerformance).where(
                SensorPerformance.sensor_id == sensor_id,
                SensorPerformance.source_paper_id == paper_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = SensorPerformance(
                sensor_id=sensor_id,
                source_paper_id=paper_id,
                is_estimated=False,
                conflicting_sources=False,
            )
            self._session.add(row)

        row.sensitivity = _dec(metric.sensitivity)
        row.specificity = _dec(metric.specificity)
        row.auc = _dec(metric.auc)
        row.lod_value = _dec(metric.lod_value)
        row.lod_unit = metric.lod_unit
        row.assay_time_minutes = _dec(metric.assay_time_minutes)
        row.sample_volume = _dec(metric.sample_volume)
        row.sample_volume_unit = metric.sample_volume_unit
        row.estimated_cost_usd = _dec(metric.estimated_cost_usd)
        row.extraction_confidence = _dec(metric.extraction_confidence)
        row.is_estimated = metric.is_estimated
        row.source_excerpt = metric.source_excerpt or None
        row.source = "literature_extraction"
        row.assay_conditions = metric.source_excerpt[:500] if metric.source_excerpt else None

        await self._session.flush()
        await self._mark_conflicting_sources(sensor_id, row)
        await self._session.flush()
        return row

    async def _mark_conflicting_sources(
        self, sensor_id: uuid.UUID, current: SensorPerformance
    ) -> None:
        """Flag performances when literature values materially disagree."""
        result = await self._session.execute(
            select(SensorPerformance).where(
                SensorPerformance.sensor_id == sensor_id,
                SensorPerformance.source_paper_id.is_not(None),
            )
        )
        rows = list(result.scalars().all())
        if len(rows) < 2:
            current.conflicting_sources = False
            return

        conflict = False
        for other in rows:
            if other.id == current.id:
                continue
            if _metrics_conflict(current, other):
                conflict = True
                other.conflicting_sources = True

        current.conflicting_sources = conflict
        if conflict:
            logger.info(
                "sensor_performance_conflict_flagged",
                sensor_id=str(sensor_id),
                performance_id=str(current.id),
            )


def _dec(value: float | None):
    from decimal import Decimal

    if value is None:
        return None
    return Decimal(str(round(value, 6)))


def _metrics_conflict(a: SensorPerformance, b: SensorPerformance) -> bool:
    """True when key metrics differ beyond tolerance across papers."""
    pairs = [
        (a.sensitivity, b.sensitivity, 0.08),
        (a.specificity, b.specificity, 0.08),
        (a.auc, b.auc, 0.08),
    ]
    for left, right, tol in pairs:
        if left is None or right is None:
            continue
        if abs(float(left) - float(right)) > tol:
            return True

    if (
        a.lod_value is not None
        and b.lod_value is not None
        and a.lod_unit
        and b.lod_unit
        and a.lod_unit.lower() == b.lod_unit.lower()
    ):
        av, bv = float(a.lod_value), float(b.lod_value)
        if av > 0 and bv > 0:
            ratio = max(av, bv) / min(av, bv)
            if ratio >= 5.0:
                return True
    return False
