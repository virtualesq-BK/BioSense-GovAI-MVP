from pydantic import BaseModel, Field


class PaperSummary(BaseModel):
    id: str
    external_id: str
    title: str
    source: str
    ingestion_status: str
    chunk_count: int
    pdf_filename: str | None
    created_at: str


class LiteratureIngestionStatus(BaseModel):
    total_papers: int
    indexed_papers: int
    pending_papers: int
    failed_papers: int
    total_chunks: int


class CitationResponse(BaseModel):
    paper_external_id: str
    paper_title: str
    chunk_id: str
    excerpt: str
    relevance_score: float


class BiomarkerRecommendationResponse(BaseModel):
    biomarker_name: str
    sensor_strategy: str
    recognition_approach: str
    rationale: str
    confidence: float
    citations: list[CitationResponse]


class RagQueryRequest(BaseModel):
    query: str = Field(min_length=3)
    cancer_type: str | None = None
    biomarker_name: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class RagQueryResponse(BaseModel):
    query: str
    cancer_type: str | None
    biomarker_name: str | None
    recommendations: list[BiomarkerRecommendationResponse]
    citations: list[CitationResponse]
    chunks_retrieved: int
    latency_ms: int


class RagEvaluateRequest(BaseModel):
    query: str = Field(min_length=3)
    expected_terms: list[str] = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class RagEvaluateResponse(BaseModel):
    evaluation_id: str
    precision_at_k: float
    recall_at_k: float
    citation_coverage: float
    mrr: float
    chunks_evaluated: int
    expected_terms: list[str]


class IngestTextRequest(BaseModel):
    external_id: str
    title: str
    text: str = Field(min_length=50)
    authors: list[str] | None = None
