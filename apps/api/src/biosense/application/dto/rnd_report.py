from pydantic import BaseModel, ConfigDict, Field

from biosense.application.dto.catalog import BiomarkerPriorityScoreResponse


class RndDesignRequest(BaseModel):
    country: str = Field(default="Korea")
    cancer: str
    biomarker_type: str | None = Field(default=None, description="ctDNA class, e.g. 'mutation'")
    target_gene: str | None = None
    goal: str
    region_code: str = "KR-00"
    patient_age: int = Field(default=50, ge=0, le=120)


class EpidemiologicalEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    region_code: str
    region_name_ko: str | None
    incidence_rate: float | None
    mortality_rate: float | None
    national_incidence_avg: float | None
    national_mortality_avg: float | None
    narrative: str
    source: str
    missing_data: bool


class MolecularCharacteristicsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    gene_symbol: str | None
    gene_name: str | None
    biotype: str | None
    mutation_count: int | None
    source: str
    missing_data: bool


class SensorCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sensor_name: str
    sensor_type: str
    recognition_code: str
    recognition_name: str
    match_score: float
    sensor_efficiency: float
    sensitivity: float | None
    specificity: float | None
    lod_value: float | None
    lod_unit: str | None
    estimated_cost_usd: float | None
    is_estimated: bool | None
    graph_path: str


class ExperimentalDesignHypothesisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    steps: list[str]
    reagents: list[str]
    duration_hours: float | None
    is_ai_suggested: bool


class ReferenceEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    external_id: str
    title: str
    source: str


class RndDesignReportResponse(BaseModel):
    target_disease: str
    goal: str
    epidemiological_evidence: EpidemiologicalEvidenceResponse
    biomarker_candidates: list[BiomarkerPriorityScoreResponse]
    selected_biomarker_name: str | None
    molecular_characteristics: MolecularCharacteristicsResponse
    recognition_strategy: str | None
    sensor_candidates: list[SensorCandidateResponse]
    existing_evidence: list[ReferenceEntryResponse]
    expected_performance: SensorCandidateResponse | None
    evidence_confidence: float
    experimental_design_hypothesis: ExperimentalDesignHypothesisResponse | None
    data_limitations: list[str]
    references: list[str]
