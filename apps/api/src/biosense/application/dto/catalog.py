from pydantic import BaseModel, ConfigDict


class CancerResponse(BaseModel):
    id: str
    code: str
    name_en: str
    name_ko: str | None
    icd_code: str | None


class BiomarkerSummaryResponse(BaseModel):
    id: str
    name: str
    gene_symbol: str | None
    ctdna_class: str
    cancer_codes: list[str]
    priority_score: float | None = None


class RecognitionMatchResponse(BaseModel):
    recognition_code: str
    recognition_name: str
    match_score: float


class PaperSummaryRefResponse(BaseModel):
    external_id: str
    title: str
    source: str


class BiomarkerDetailResponse(BaseModel):
    id: str
    name: str
    gene_symbol: str | None
    ctdna_class: str
    description: str | None
    cancer_codes: list[str]
    recognition_matches: list[RecognitionMatchResponse]
    papers: list[PaperSummaryRefResponse]


class ScoreComponentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score: float
    evidence: str
    source: str
    confidence: float
    missing_data: bool


class BiomarkerPriorityScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    biomarker_name: str
    cancer_type: str
    total_score: float
    disease_burden: ScoreComponentResponse
    molecular_evidence: ScoreComponentResponse
    clinical_evidence: ScoreComponentResponse
    detection_feasibility: ScoreComponentResponse
    sensor_compatibility: ScoreComponentResponse
    data_confidence: ScoreComponentResponse
    missing_data_factors: list[str]
