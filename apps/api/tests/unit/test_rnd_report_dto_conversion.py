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
