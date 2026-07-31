import json
import time
import uuid
from dataclasses import asdict
from pathlib import Path

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.application.services.chunking_service import ChunkingService
from biosense.config import settings
from biosense.domain.entities.literature import (
    BiomarkerRecommendation,
    Citation,
    ParsedPaper,
)
from biosense.infrastructure.ai.embedding_service import EmbeddingService
from biosense.infrastructure.ai.pdf_parser import PdfParser
from biosense.infrastructure.persistence.postgres.literature_repository import LiteratureRepository

logger = structlog.get_logger()


class LiteratureIngestionPipeline:
    """PDF → parse → chunk → embed → store in pgvector."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = LiteratureRepository(session)
        self._parser = PdfParser()
        self._chunker = ChunkingService()
        self._embedder = EmbeddingService()
        self._session = session

    async def ingest_pdf_bytes(
        self,
        data: bytes,
        *,
        external_id: str,
        title: str,
        filename: str,
        authors: list[str] | None = None,
    ) -> uuid.UUID:
        upload_dir = Path(settings.literature_upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{external_id.replace(':', '_')}_{filename}"
        (upload_dir / safe_name).write_bytes(data)

        existing = await self._repo.get_paper_by_external_id(external_id)
        if existing:
            paper = existing
            paper.title = title
            paper.pdf_filename = safe_name
            paper.ingestion_status = "pending"
        else:
            paper = await self._repo.create_paper(
                external_id=external_id,
                title=title,
                pdf_filename=safe_name,
                authors=authors,
            )

        job = await self._repo.create_ingestion_job(paper.id)
        await self._session.commit()

        try:
            await self._repo.mark_ingestion_running(job.id)
            await self._session.commit()

            parsed = self._parser.parse_bytes(data, title=title)
            paper.abstract = parsed.abstract
            chunks = self._chunker.chunk_paper(parsed, external_id)
            embeddings = await self._embedder.embed_texts([c.content for c in chunks])
            count = await self._repo.replace_chunks(paper.id, chunks, embeddings)
            await self._repo.complete_ingestion(job.id, paper.id, count)
            await self._session.commit()
            logger.info("literature_ingested", paper_id=str(paper.id), chunks=count)
            return paper.id
        except Exception as exc:
            await self._repo.fail_ingestion(job.id, paper.id, str(exc))
            await self._session.commit()
            raise

    async def reingest_paper(self, paper_id: uuid.UUID) -> uuid.UUID:
        paper = await self._repo.get_paper(paper_id)
        if not paper or not paper.pdf_filename:
            raise ValueError("Paper not found or no PDF uploaded")

        path = Path(settings.literature_upload_dir) / paper.pdf_filename
        data = path.read_bytes()
        return await self.ingest_pdf_bytes(
            data,
            external_id=paper.external_id,
            title=paper.title,
            filename=paper.pdf_filename,
            authors=paper.authors,
        )

    async def ingest_text(
        self,
        *,
        external_id: str,
        title: str,
        text: str,
        authors: list[str] | None = None,
    ) -> uuid.UUID:
        existing = await self._repo.get_paper_by_external_id(external_id)
        if existing:
            paper = existing
            paper.ingestion_status = "pending"
        else:
            paper = await self._repo.create_paper(
                external_id=external_id, title=title, authors=authors, source="text"
            )

        job = await self._repo.create_ingestion_job(paper.id)
        await self._session.commit()

        try:
            await self._repo.mark_ingestion_running(job.id)
            await self._session.commit()

            parsed = ParsedPaper(title=title, text=text, page_count=1)
            chunks = self._chunker.chunk_paper(parsed, external_id)
            embeddings = await self._embedder.embed_texts([c.content for c in chunks])
            count = await self._repo.replace_chunks(paper.id, chunks, embeddings)
            await self._repo.complete_ingestion(job.id, paper.id, count)
            await self._session.commit()
            return paper.id
        except Exception as exc:
            await self._repo.fail_ingestion(job.id, paper.id, str(exc))
            await self._session.commit()
            raise
