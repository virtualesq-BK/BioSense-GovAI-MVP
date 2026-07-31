from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedPaper:
    title: str
    text: str
    page_count: int
    abstract: str | None = None


@dataclass(frozen=True)
class TextChunk:
    index: int
    content: str
    metadata: dict[str, object]


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    paper_id: str
    paper_external_id: str
    paper_title: str
    content: str
    score: float
    chunk_index: int


@dataclass(frozen=True)
class Citation:
    paper_external_id: str
    paper_title: str
    chunk_id: str
    excerpt: str
    relevance_score: float


@dataclass(frozen=True)
class BiomarkerRecommendation:
    biomarker_name: str
    sensor_strategy: str
    recognition_approach: str
    rationale: str
    confidence: float
    citations: list[Citation]
