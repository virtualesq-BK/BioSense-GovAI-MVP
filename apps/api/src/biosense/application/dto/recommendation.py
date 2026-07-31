from pydantic import BaseModel, Field


class GenerateRecommendationRequest(BaseModel):
    cancer_type: str
    ctdna_class: str
    region_code: str
    patient_age: int = Field(ge=0, le=120)
    biomarker_name: str | None = None
    notes: str | None = None
    top_k: int = Field(default=3, ge=1, le=10)


class ExpectedMetricsResponse(BaseModel):
    sensitivity: float
    specificity: float
    lod_value: float
    lod_unit: str
    estimated_cost_usd: float


class SensorRecommendationResponse(BaseModel):
    rank: int
    sensor_type: str
    sensor_name: str
    recognition_strategy: str
    recognition_name: str
    biomarker_name: str
    expected_metrics: ExpectedMetricsResponse
    experimental_protocol: dict
    confidence_score: float
    composite_score: float
    rationale: str
    evidence: dict


class GenerateRecommendationResponse(BaseModel):
    recommendations: list[SensorRecommendationResponse]
    count: int
