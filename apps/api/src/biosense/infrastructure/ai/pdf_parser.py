from io import BytesIO
from pathlib import Path

import structlog
from pypdf import PdfReader

from biosense.domain.entities.literature import ParsedPaper

logger = structlog.get_logger()


class PdfParser:
    """Extract text from scientific PDF papers."""

    def parse_bytes(self, data: bytes, title: str = "Untitled") -> ParsedPaper:
        reader = PdfReader(BytesIO(data))
        pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())

        full_text = "\n\n".join(pages)
        abstract = _extract_abstract(full_text)
        logger.info("pdf_parsed", title=title, pages=len(reader.pages), chars=len(full_text))
        return ParsedPaper(
            title=title,
            text=full_text,
            page_count=len(reader.pages),
            abstract=abstract,
        )

    def parse_file(self, path: Path, title: str | None = None) -> ParsedPaper:
        data = path.read_bytes()
        return self.parse_bytes(data, title=title or path.stem)


def _extract_abstract(text: str) -> str | None:
    lowered = text.lower()
    for marker in ("abstract", "summary"):
        idx = lowered.find(marker)
        if idx == -1:
            continue
        snippet = text[idx : idx + 1500]
        if len(snippet) > 50:
            return snippet.strip()
    return None
