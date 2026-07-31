import re

import structlog

from biosense.config import settings
from biosense.domain.entities.literature import ParsedPaper, TextChunk

logger = structlog.get_logger()


class ChunkingService:
    """Split paper text into overlapping chunks for embedding."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        self._chunk_size = chunk_size or settings.literature_chunk_size
        self._overlap = chunk_overlap or settings.literature_chunk_overlap

    def chunk_paper(self, paper: ParsedPaper, paper_external_id: str) -> list[TextChunk]:
        text = _normalize_whitespace(paper.text)
        if not text:
            return []

        chunks: list[TextChunk] = []
        start = 0
        index = 0
        while start < len(text):
            end = min(start + self._chunk_size, len(text))
            if end < len(text):
                boundary = _find_boundary(text, start, end)
                if boundary > start:
                    end = boundary

            content = text[start:end].strip()
            if content:
                chunks.append(
                    TextChunk(
                        index=index,
                        content=content,
                        metadata={
                            "paper_external_id": paper_external_id,
                            "title": paper.title,
                            "page_count": paper.page_count,
                        },
                    )
                )
                index += 1

            if end >= len(text):
                break
            start = max(end - self._overlap, start + 1)

        logger.info("chunking_complete", chunks=len(chunks), paper=paper_external_id)
        return chunks


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _find_boundary(text: str, start: int, end: int) -> int:
    segment = text[start:end]
    min_pos = max(0, (end - start) // 3)
    for sep in (". ", ".\n", "\n"):
        pos = segment.rfind(sep)
        if pos > min_pos:
            return start + pos + len(sep)
    return end
