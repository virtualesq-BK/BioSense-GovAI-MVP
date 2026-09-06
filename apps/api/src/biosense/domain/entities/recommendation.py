from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class RecommendationInput:
    cancer_type: str
    ctdna_class: str
    region_code: str
    patient_age: int
    biomarker_name: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class ExtractedFeatures:
    cancer_type: str
    ctdna_class: str
    region_code: str
    patient_age: int
    incidence_rate: float | None
    mortality_rate: float | None
    age_risk_factor: float
    public_health_score: float
    query_text: str
    biomarker_hints: list[str] = field(default_factory=list)
    public_health_narrative: str = ""
    national_incidence_avg: float | None = None
    national_mortality_avg: float | None = None
    region_name_ko: str | None = None


@dataclass(frozen=True)
class PublicHealthSnapshot:
    """Regional rates plus national aggregates for narrative templates."""

    incidence_rate: float | None
    mortality_rate: float | None
    public_health_score: float
    national_incidence_avg: float | None = None
    national_mortality_avg: float | None = None
    region_name_ko: str | None = None
    region_code: str = ""



@dataclass(frozen=True)
class GraphCandidate:
    biomarker_id: str
    biomarker_name: str
    recognition_id: str
    recognition_code: str
    recognition_name: str
    sensor_id: str
    sensor_name: str
    sensor_type: str
    match_score: float
    sensor_efficiency: float
    sensitivity: float | None
    specificity: float | None
    lod_value: float | None
    lod_unit: str | None
    estimated_cost_usd: float | None
    protocol_steps: list[str]
    graph_path: str
    conflicting_sources: bool = False


@dataclass
class ScoredCandidate:
    candidate: GraphCandidate
    literature_score: float
    composite_score: float
    confidence: float
    literature_citations: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class ExpectedMetrics:
    sensitivity: float
    specificity: float
    lod_value: float
    lod_unit: str
    estimated_cost_usd: float


@dataclass(frozen=True)
class SensorRecommendation:
    rank: int
    sensor_type: str
    sensor_name: str
    recognition_strategy: str
    recognition_name: str
    biomarker_name: str
    expected_metrics: ExpectedMetrics
    experimental_protocol: dict
    confidence_score: float
    composite_score: float
    rationale: str
    evidence: dict
