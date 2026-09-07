from biosense.api.v1.rnd import _to_response
from biosense.domain.entities.priority_score import BiomarkerPriorityScore, ScoreComponent
from biosense.domain.entities.rnd_report import (
    EpidemiologicalEvidence,
    ExperimentalDesignHypothesis,
    MolecularCharacteristics,
    ReferenceEntry,
    RndDesignReport,
    SensorCandidate,
)


def _component(score: float = 50.0) -> ScoreComponent:
    return ScoreComponent(score=score, evidence="e", source="s", confidence=0.5)


def _priority_score() -> BiomarkerPriorityScore:
    return BiomarkerPriorityScore(
        biomarker_name="KRAS G12D mutation",
        cancer_type="lung",
        total_score=66.4,
        disease_burden=_component(),
        molecular_evidence=_component(),
        clinical_evidence=_component(),
        detection_feasibility=_component(),
        sensor_compatibility=_component(),
        data_confidence=_component(),
    )


def test_to_response_converts_full_report() -> None:
    sensor = SensorCandidate(
        sensor_name="AI-NGS liquid biopsy analyzer",
        sensor_type="AI_NGS",
        recognition_code="dna_hybridization",
        recognition_name="DNA hybridization probe",
        match_score=0.93,
        sensor_efficiency=0.93,
        sensitivity=0.94,
        specificity=0.96,
        lod_value=0.001,
        lod_unit="ng/mL",
        estimated_cost_usd=450.0,
        is_estimated=True,
        graph_path="Cancer->KRAS G12D mutation->dna_hybridization->AI_NGS",
    )
    report = RndDesignReport(
        target_disease="Lung Cancer",
        goal="early detection",
        epidemiological_evidence=EpidemiologicalEvidence(
            region_code="KR-11",
            region_name_ko="서울특별시",
            incidence_rate=42.5,
            mortality_rate=28.3,
            national_incidence_avg=43.6,
            national_mortality_avg=27.8,
            narrative="",
            source="KOSIS/KDCA",
            missing_data=False,
        ),
        biomarker_candidates=[_priority_score()],
        selected_biomarker_name="KRAS G12D mutation",
        molecular_characteristics=MolecularCharacteristics(
            gene_symbol="KRAS",
            gene_name="KRAS proto-oncogene",
            biotype="protein_coding",
            mutation_count=141,
            source="NCI GDC",
            missing_data=False,
        ),
        recognition_strategy="dna_hybridization",
        sensor_candidates=[sensor],
        existing_evidence=[
            ReferenceEntry(external_id="pmid:123", title="A Paper", source="PubMed")
        ],
        expected_performance=sensor,
        evidence_confidence=66.4,
        experimental_design_hypothesis=ExperimentalDesignHypothesis(
            steps=["step 1"], reagents=["buffer"], duration_hours=6.0, is_ai_suggested=True
        ),
        data_limitations=["For research support only."],
        references=["PubMed:pmid:123 — A Paper"],
    )

    response = _to_response(report)

    # Phase 1 fields default to empty/None when not populated by the service.
    assert response.phase1_molecular_characterization is None
    assert response.phase1_recognition_recommendations == []
    assert response.phase1_sensor_transduction_candidates == []
    assert response.phase1_composite_score is None

    assert response.target_disease == "Lung Cancer"
    assert response.selected_biomarker_name == "KRAS G12D mutation"
    assert response.biomarker_candidates[0].total_score == 66.4
    assert response.sensor_candidates[0].sensor_name == "AI-NGS liquid biopsy analyzer"
    assert response.expected_performance.is_estimated is True
    assert response.experimental_design_hypothesis.is_ai_suggested is True
    assert response.existing_evidence[0].external_id == "pmid:123"


def test_to_response_handles_no_biomarker_found() -> None:
    report = RndDesignReport(
        target_disease="Lung Cancer",
        goal="early detection",
        epidemiological_evidence=EpidemiologicalEvidence(
            region_code="KR-00",
            region_name_ko=None,
            incidence_rate=None,
            mortality_rate=None,
            national_incidence_avg=None,
            national_mortality_avg=None,
            narrative="",
            source="none",
            missing_data=True,
        ),
        biomarker_candidates=[],
        selected_biomarker_name=None,
        molecular_characteristics=MolecularCharacteristics(
            gene_symbol=None,
            gene_name=None,
            biotype=None,
            mutation_count=None,
            source="none",
            missing_data=True,
        ),
        recognition_strategy=None,
        sensor_candidates=[],
        existing_evidence=[],
        expected_performance=None,
        evidence_confidence=0.0,
        experimental_design_hypothesis=None,
        data_limitations=["No biomarker candidates found."],
        references=[],
    )

    response = _to_response(report)

    assert response.selected_biomarker_name is None
    assert response.expected_performance is None
    assert response.experimental_design_hypothesis is None
    assert response.sensor_candidates == []


def test_to_response_converts_phase1_sections_when_populated() -> None:
    from biosense.domain.entities.biomarker_dimension import EvidenceRef
    from biosense.domain.entities.molecular_characterization import (
        Detectability,
        MolecularCharacterizationResult,
    )
    from biosense.domain.entities.molecular_recognition import (
        RecognitionRecommendation,
        RecognitionStrategyType,
    )
    from biosense.domain.entities.rd_scoring import RdCompositeScore, RdScoreFactor
    from biosense.domain.entities.sensor_transduction import (
        SensorPlatformType,
        SensorTransductionCandidate,
    )

    molecular = MolecularCharacterizationResult(
        biomarker="KRAS G12D mutation",
        dimension="mutation",
        molecular_characteristics=["Target gene KRAS"],
        detectability=Detectability(True, 141, "basis", False),
        specificity_features=["specific"],
        limitations=["Research use only."],
        evidence=[EvidenceRef(source="NCI GDC", external_id="ENSG1", title="KRAS")],
    )
    recognition = [
        RecognitionRecommendation(
            strategy=RecognitionStrategyType.DNA_HYBRIDIZATION,
            status="scored",
            compatibility_score=80.0,
            rationale="r",
            confidence=0.7,
        )
    ]
    sensors = [
        SensorTransductionCandidate(
            platform=SensorPlatformType.ELECTROCHEMICAL,
            status="scored",
            sensor_name="EC sensor",
            feasibility_score=75.0,
            rationale="r",
        )
    ]

    def factor(score):
        return RdScoreFactor(score=score, basis="basis")

    composite = RdCompositeScore(
        biomarker_name="KRAS G12D mutation",
        molecular_fit=factor(70.0),
        recognition_feasibility=factor(80.0),
        sensor_feasibility=factor(75.0),
        published_evidence=factor(25.0),
        clinical_relevance=factor(50.0),
        data_confidence=factor(50.0),
        weights={"molecular_fit": 1.0},
        total_score=64.75,
    )

    report = RndDesignReport(
        target_disease="Lung Cancer",
        goal="early detection",
        epidemiological_evidence=EpidemiologicalEvidence(
            region_code="KR-00",
            region_name_ko=None,
            incidence_rate=None,
            mortality_rate=None,
            national_incidence_avg=None,
            national_mortality_avg=None,
            narrative="",
            source="none",
            missing_data=True,
        ),
        biomarker_candidates=[],
        selected_biomarker_name="KRAS G12D mutation",
        molecular_characteristics=MolecularCharacteristics(
            gene_symbol="KRAS",
            gene_name="KRAS",
            biotype="protein_coding",
            mutation_count=141,
            source="NCI GDC",
            missing_data=False,
        ),
        recognition_strategy="dna_hybridization",
        sensor_candidates=[],
        existing_evidence=[],
        expected_performance=None,
        evidence_confidence=64.75,
        experimental_design_hypothesis=None,
        data_limitations=[],
        references=[],
        phase1_molecular_characterization=molecular,
        phase1_recognition_recommendations=recognition,
        phase1_sensor_transduction_candidates=sensors,
        phase1_composite_score=composite,
        phase1_disclaimers=["Research use only — not a diagnostic system."],
    )

    response = _to_response(report)

    assert response.phase1_molecular_characterization.dimension == "mutation"
    assert response.phase1_molecular_characterization.evidence[0].source == "NCI GDC"
    assert response.phase1_recognition_recommendations[0].strategy == "dna_hybridization"
    assert response.phase1_sensor_transduction_candidates[0].platform == "electrochemical"
    assert response.phase1_composite_score.total_score == 64.75
    assert "Research use only" in response.phase1_disclaimers[0]
