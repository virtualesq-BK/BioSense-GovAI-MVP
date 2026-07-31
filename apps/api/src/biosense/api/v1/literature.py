import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.api.dependencies import get_db_session
from biosense.application.dto.literature import (
    BiomarkerRecommendationResponse,
    CitationResponse,
    IngestTextRequest,
    LiteratureIngestionStatus,
    PaperSummary,
    RagEvaluateRequest,
    RagEvaluateResponse,
    RagQueryRequest,
    RagQueryResponse,
)
from biosense.application.services.literature_ingestion_service import LiteratureIngestionPipeline
from biosense.application.services.literature_rag_service import (
    LiteratureEvaluationService,
    LiteratureRagQueryService,
)
from biosense.infrastructure.persistence.postgres.literature_repository import LiteratureRepository

router = APIRouter(tags=["Literature RAG"])


@router.get("/literature/papers", response_model=list[PaperSummary])
async def list_papers(
    session: AsyncSession = Depends(get_db_session),
) -> list[PaperSummary]:
    repo = LiteratureRepository(session)
    papers = await repo.list_papers()
    return [_paper_to_summary(p) for p in papers]


@router.get("/literature/papers/{paper_id}", response_model=PaperSummary)
async def get_paper(
    paper_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> PaperSummary:
    repo = LiteratureRepository(session)
    paper = await repo.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return _paper_to_summary(paper)


@router.post("/literature/papers/upload", response_model=PaperSummary)
async def upload_paper_pdf(
    file: UploadFile = File(...),
    external_id: str = Form(...),
    title: str = Form(...),
    authors: str = Form(""),
    session: AsyncSession = Depends(get_db_session),
) -> PaperSummary:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    data = await file.read()
    author_list = [a.strip() for a in authors.split(",") if a.strip()] or None
    pipeline = LiteratureIngestionPipeline(session)
    paper_id = await pipeline.ingest_pdf_bytes(
        data,
        external_id=external_id,
        title=title,
        filename=file.filename,
        authors=author_list,
    )
    repo = LiteratureRepository(session)
    paper = await repo.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=500, detail="Ingestion failed")
    return _paper_to_summary(paper)


@router.post("/literature/papers/ingest-text", response_model=PaperSummary)
async def ingest_paper_text(
    body: IngestTextRequest,
    session: AsyncSession = Depends(get_db_session),
) -> PaperSummary:
    pipeline = LiteratureIngestionPipeline(session)
    paper_id = await pipeline.ingest_text(
        external_id=body.external_id,
        title=body.title,
        text=body.text,
        authors=body.authors,
    )
    repo = LiteratureRepository(session)
    paper = await repo.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=500, detail="Ingestion failed")
    return _paper_to_summary(paper)


@router.post("/literature/papers/{paper_id}/reingest", response_model=PaperSummary)
async def reingest_paper(
    paper_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
) -> PaperSummary:
    pipeline = LiteratureIngestionPipeline(session)
    try:
        new_id = await pipeline.reingest_paper(paper_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    repo = LiteratureRepository(session)
    paper = await repo.get_paper(new_id)
    return _paper_to_summary(paper)


@router.get("/literature/ingestion/status", response_model=LiteratureIngestionStatus)
async def get_ingestion_status(
    session: AsyncSession = Depends(get_db_session),
) -> LiteratureIngestionStatus:
    try:
        repo = LiteratureRepository(session)
        stats = await repo.get_ingestion_stats()
        return LiteratureIngestionStatus(**stats)
    except Exception:
        # Keep UI responsive when DB is unavailable.
        return LiteratureIngestionStatus(
            total_papers=0,
            indexed_papers=0,
            pending_papers=0,
            failed_papers=0,
            total_chunks=0,
        )


@router.post("/literature/rag/query", response_model=RagQueryResponse)
async def rag_query(
    body: RagQueryRequest,
    session: AsyncSession = Depends(get_db_session),
) -> RagQueryResponse:
    service = LiteratureRagQueryService(session)
    result = await service.query(
        body.query,
        cancer_type=body.cancer_type,
        biomarker_name=body.biomarker_name,
        top_k=body.top_k,
    )
    await session.commit()
    return RagQueryResponse(
        query=result["query"],
        cancer_type=result["cancer_type"],
        biomarker_name=result["biomarker_name"],
        recommendations=[BiomarkerRecommendationResponse(**r) for r in result["recommendations"]],
        citations=[CitationResponse(**c) for c in result["citations"]],
        chunks_retrieved=result["chunks_retrieved"],
        latency_ms=result["latency_ms"],
    )


@router.post("/literature/rag/evaluate", response_model=RagEvaluateResponse)
async def rag_evaluate(
    body: RagEvaluateRequest,
    session: AsyncSession = Depends(get_db_session),
) -> RagEvaluateResponse:
    service = LiteratureEvaluationService(session)
    result = await service.evaluate(
        body.query, expected_terms=body.expected_terms, top_k=body.top_k
    )
    await session.commit()
    return RagEvaluateResponse(**result)


@router.get("/literature/rag/evaluations", response_model=list[RagEvaluateResponse])
async def list_evaluations(
    session: AsyncSession = Depends(get_db_session),
) -> list[RagEvaluateResponse]:
    repo = LiteratureRepository(session)
    evals = await repo.list_evaluations()
    return [
        RagEvaluateResponse(
            evaluation_id=str(e.id),
            precision_at_k=float(e.precision_at_k or 0),
            recall_at_k=float(e.recall_at_k or 0),
            citation_coverage=float(e.citation_coverage or 0),
            mrr=float(e.mrr or 0),
            chunks_evaluated=e.chunks_evaluated,
            expected_terms=e.details.get("expected_terms", []),
        )
        for e in evals
    ]


def _paper_to_summary(paper) -> PaperSummary:
    return PaperSummary(
        id=str(paper.id),
        external_id=paper.external_id,
        title=paper.title,
        source=paper.source,
        ingestion_status=paper.ingestion_status,
        chunk_count=paper.chunk_count,
        pdf_filename=paper.pdf_filename,
        created_at=paper.created_at.isoformat(),
    )
