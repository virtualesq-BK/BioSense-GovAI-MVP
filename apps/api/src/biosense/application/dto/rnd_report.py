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


class EvidenceRefResponse(BaseModel):
    source: str
    external_id: str
    title: str
    dataset: str | None = None
    original_identifier: str | None = None
    access_date: str | None = None
    access_level: str | None = None
    evidence_type: str | None = None


class DetectabilityResponse(BaseModel):
    is_detectable_in_ctdna: bool | None
    mutation_count: int | None
    basis: str
    missing_data: bool


class MolecularCharacterizationResponse(BaseModel):
    biomarker: str
    dimension: str
    molecular_characteristics: list[str]
    detectability: DetectabilityResponse | None
    specificity_features: list[str]
    limitations: list[str]
    evidence: list[EvidenceRefResponse]
    evidence_status: str | None = None
    evidence_status_reason: str | None = None


class MolecularDetectabilityResponse(BaseModel):
    biomarker: str
    dimension: str
    abundance: float | None
    allele_fraction: float | None
    sequence_specificity: str
    chemical_distinguishability: str
    structural_signal: str
    sample_compatibility: str
    background_interference: str
    detectability_confidence: float
    basis: str
    evidence: list[EvidenceRefResponse]
    limitations: list[str]


class RecognitionRecommendationResponse(BaseModel):
    strategy: str
    status: str
    compatibility_score: float | None
    rationale: str
    supporting_evidence: list[str]
    limitations: list[str]
    confidence: float | None
    computation_basis: dict
    evidence_source: str = "HEURISTIC"
    citation_evidence: list[dict] = []


class SensorTransductionCandidateResponse(BaseModel):
    platform: str
    status: str
    sensor_name: str | None
    feasibility_score: float | None
    rationale: str
    sensitivity: float | None
    specificity: float | None
    lod_value: float | None
    lod_unit: str | None
    is_estimated: bool | None
    limitations: list[str]
    supporting_evidence: list[str]


class RdScoreFactorResponse(BaseModel):
    score: float
    basis: str
    missing_data: bool


class RdCompositeScoreResponse(BaseModel):
    biomarker_name: str
    molecular_fit: RdScoreFactorResponse
    recognition_feasibility: RdScoreFactorResponse
    sensor_feasibility: RdScoreFactorResponse
    published_evidence: RdScoreFactorResponse
    clinical_relevance: RdScoreFactorResponse
    data_confidence: RdScoreFactorResponse
    weights: dict[str, float]
    total_score: float


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

    phase1_molecular_characterization: MolecularCharacterizationResponse | None = None
    phase1_detectability: MolecularDetectabilityResponse | None = None
    phase1_recognition_recommendations: list[RecognitionRecommendationResponse] = Field(
        default_factory=list
    )
    phase1_sensor_transduction_candidates: list[SensorTransductionCandidateResponse] = Field(
        default_factory=list
    )
    phase1_composite_score: RdCompositeScoreResponse | None = None
    phase1_disclaimers: list[str] = Field(default_factory=list)
