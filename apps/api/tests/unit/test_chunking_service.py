from biosense.application.services.chunking_service import ChunkingService
from biosense.domain.entities.literature import ParsedPaper


def test_chunking_produces_multiple_chunks() -> None:
    text = "word " * 300
    paper = ParsedPaper(title="Test", text=text, page_count=1)
    chunks = ChunkingService(chunk_size=100, chunk_overlap=20).chunk_paper(paper, "pmid:test")
    assert len(chunks) > 1
    assert chunks[0].index == 0
    assert all(c.content for c in chunks)


def test_chunking_empty_text() -> None:
    paper = ParsedPaper(title="Empty", text="   ", page_count=0)
    chunks = ChunkingService().chunk_paper(paper, "pmid:empty")
    assert chunks == []
