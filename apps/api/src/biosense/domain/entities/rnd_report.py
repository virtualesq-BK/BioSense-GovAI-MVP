"""Domain value objects for the R&D Design Report (§13/§22).

Every numeric claim in this report traces back to a real query result — Postgres
domain graph, live GDC, or the Biomarker Priority Score — never a value invented to
fill a gap. Where evidence doesn't exist, the corresponding field is None/empty and
`data_limitations` says so explicitly.
"""

from dataclasses import dataclass, field

from biosense.domain.entities.molecular_characterization import MolecularCharacterizationResult
from biosense.domain.entities.molecular_detectability import MolecularDetectabilityResult
from biosense.domain.entities.molecular_recognition import RecognitionRecommendation
from biosense.domain.entities.rd_scoring import RdCompositeScore
from biosense.domain.entities.sensor_transduction import SensorTransductionCandidate


@dataclass(frozen=True)
class RndDesignInput:
    country: str
    cancer: str
    biomarker_type: str | None  # ctdna_class, e.g. "mutation", "methylation"
    target_gene: str | None
    goal: str
    region_code: str = "KR-00"
    patient_age: int = 50


@dataclass(frozen=True)
class EpidemiologicalEvidence:
    region_code: str
    region_name_ko: str | None
    incidence_rate: float | None
    mortality_rate: float | None
    national_incidence_avg: float | None
    national_mortality_avg: float | None
    narrative: str
    source: str
    missing_data: bool


@dataclass(frozen=True)
class MolecularCharacteristics:
    gene_symbol: str | None
    gene_name: str | None
    biotype: str | None
    mutation_count: int | None
    source: str
    missing_data: bool


@dataclass(frozen=True)
class SensorCandidate:
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
    is_estimated: bool | None  # None = no performance record at all
    graph_path: str


@dataclass(frozen=True)
class ExperimentalDesignHypothesis:
    steps: list[str]
    reagents: list[str]
    duration_hours: float | None
    is_ai_suggested: bool


@dataclass(frozen=True)
class ReferenceEntry:
    external_id: str
    title: str
    source: str


@dataclass(frozen=True)
class RndDesignReport:
    target_disease: str
    goal: str
    epidemiological_evidence: EpidemiologicalEvidence
    biomarker_candidates: list  # list[BiomarkerPriorityScore], ranked
    selected_biomarker_name: str | None
    molecular_characteristics: MolecularCharacteristics
    recognition_strategy: str | None
    sensor_candidates: list[SensorCandidate]
    existing_evidence: list[ReferenceEntry]
    expected_performance: SensorCandidate | None
    evidence_confidence: float  # 0-100
    experimental_design_hypothesis: ExperimentalDesignHypothesis | None
    data_limitations: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)

    # --- Phase 1 (Global Multi-Omics Bio R&D Infrastructure) additions ---
    # Mutation/ctDNA dimension: Molecular Characterization -> Molecular Recognition
    # (DNA hybridization / CRISPR-Cas) -> Sensor Transduction (electrochemical) ->
    # composite score. All optional/None when Phase 1 doesn't apply (e.g. a
    # non-mutation biomarker or no candidate at all) — never backfilled with guesses.
    phase1_molecular_characterization: MolecularCharacterizationResult | None = None
    phase1_detectability: MolecularDetectabilityResult | None = None
    phase1_recognition_recommendations: list[RecognitionRecommendation] = field(
        default_factory=list
    )
    phase1_sensor_transduction_candidates: list[SensorTransductionCandidate] = field(
        default_factory=list
    )
    phase1_composite_score: RdCompositeScore | None = None
    phase1_disclaimers: list[str] = field(default_factory=list)
