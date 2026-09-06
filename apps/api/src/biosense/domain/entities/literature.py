from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ParsedPaper:
    title: str
    text: str
    page_count: int
    abstract: str | None = None


@dataclass(frozen=True)
class RawPaperRecord:
    external_id: str
    title: str
    abstract: str
    journal: str | None
    published_at: date | None
    doi: str | None
    authors: list[str]


@dataclass(frozen=True)
class ExtractedMetric:
    """Domain value object for paper-extracted sensor performance metrics."""

    sensitivity: float | None = None
    specificity: float | None = None
    auc: float | None = None
    lod_value: float | None = None
    lod_unit: str | None = None
    assay_time_minutes: float | None = None
    sample_volume: float | None = None
    sample_volume_unit: str | None = None
    estimated_cost_usd: float | None = None
    sensor_name_hint: str | None = None
    sensor_type_hint: str | None = None
    extraction_confidence: float = 0.5
    source_excerpt: str = ""
    is_estimated: bool = False


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
