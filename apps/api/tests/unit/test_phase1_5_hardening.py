"""Tests for Phase 1.5 scientific architecture hardening.

Covers: biomarker->characterization->detectability->recognition->sensor data
flow, evidence provenance fields, confidence-calculation correctness,
missing-evidence handling, stub protection, global source metadata, and —
most importantly — the regression guarantee that INSUFFICIENT_EVIDENCE can
never produce an inflated confidence or score.
"""

from types import SimpleNamespace

import pytest

from biosense.application.services.molecular_characterization_service import (
    MolecularCharacterizationService,
)
from biosense.application.services.molecular_detectability_service import (
    MolecularDetectabilityService,
)
from biosense.application.services.molecular_recognition_service import MolecularRecognitionEngine
from biosense.application.services.rd_scoring_service import RdScoringService
from biosense.domain.entities.biomarker_dimension import BiomarkerEvidenceStatus, EvidenceRef
from biosense.domain.entities.molecular_characterization import (
    Detectability,
    MolecularCharacterizationResult,
)
from biosense.domain.entities.molecular_detectability import UNKNOWN
from biosense.domain.entities.molecular_recognition import RecognitionStrategyType
from biosense.domain.entities.recognition_compatibility import RecognitionCompatibilityTable
from biosense.infrastructure.external.source_registry import DATA_SOURCES, sources_for_layer


class FakeGdcClient:
    def __init__(self, genes=None, mutation_count=None):
        self._genes = genes or []
        self._mutation_count = mutation_count

    async def search_genes(self, symbol, *, size: int = 5):
        return self._genes

    async def count_mutations_for_gene(self, gene_symbol):
        return self._mutation_count


def _biomarker(*, gene_symbol="KRAS", ctdna_code="mutation", papers=None, description=None):
    return SimpleNamespace(
        id="b1",
        name="KRAS G12D mutation",
        gene_symbol=gene_symbol,
        description=description,
        ctdna=SimpleNamespace(code=ctdna_code) if ctdna_code else None,
        papers=papers or [],
    )


def _characterization(*, detectable=True, mutation_count=5, evidence_count=2):
    evidence = [
        EvidenceRef(source="PubMed", external_id=f"pmid:{i}", title=f"Paper {i}")
        for i in range(evidence_count)
    ]
    return MolecularCharacterizationResult(
        biomarker="KRAS G12D mutation",
        dimension="mutation",
        molecular_characteristics=["some characteristic"],
        detectability=Detectability(
            is_detectable_in_ctdna=detectable,
            mutation_count=mutation_count,
            basis="test",
            missing_data=False,
        ),
        specificity_features=[],
        limitations=[],
        evidence=evidence,
        evidence_status=BiomarkerEvidenceStatus.SUPPORTED,
        evidence_status_reason="test fixture",
    )


# --- biomarker -> characterization ------------------------------------------------


@pytest.mark.asyncio
async def test_characterization_sets_supported_status_with_full_real_data():
    gene = SimpleNamespace(gene_id="ENSG1", name="KRAS proto-oncogene", biotype="protein_coding")
    gdc = FakeGdcClient(genes=[gene], mutation_count=141)
    paper = SimpleNamespace(source="PubMed", external_id="pmid:1", title="A paper")
    biomarker = _biomarker(papers=[paper])

    service = MolecularCharacterizationService(gdc=gdc)
    result = await service.characterize(biomarker, cancer_code="lung")

    assert result.evidence_status == BiomarkerEvidenceStatus.SUPPORTED
    assert result.evidence_status_reason


@pytest.mark.asyncio
async def test_characterization_sets_insufficient_evidence_status_with_no_data():
    gdc = FakeGdcClient(genes=[], mutation_count=None)
    biomarker = _biomarker(gene_symbol=None, papers=[])

    service = MolecularCharacterizationService(gdc=gdc)
    result = await service.characterize(biomarker, cancer_code="lung")

    assert result.evidence_status == BiomarkerEvidenceStatus.INSUFFICIENT_EVIDENCE


@pytest.mark.asyncio
async def test_characterization_unsupported_dimension_is_planned_not_guessed():
    # "methylation" is now handled by a dedicated Phase 2 metadata-only path
    # (see test_phase2_methylation_and_crispr_citations.py) — this test covers
    # a dimension that is still genuinely unimplemented, e.g. "fusion".
    service = MolecularCharacterizationService(gdc=FakeGdcClient())
    biomarker = _biomarker(ctdna_code="fusion")

    result = await service.characterize(biomarker, cancer_code="lung")

    assert result.evidence_status == BiomarkerEvidenceStatus.PLANNED
    assert result.molecular_characteristics == []


# --- characterization -> detectability ---------------------------------------------


def test_detectability_derives_from_real_characterization_inputs():
    characterization = _characterization(detectable=True, mutation_count=141, evidence_count=2)
    service = MolecularDetectabilityService()

    result = service.assess(characterization)

    assert result.abundance == 141.0
    assert result.sample_compatibility != UNKNOWN
    # Never fabricated: no data source feeds these, so they must stay unknown.
    assert result.allele_fraction is None
    assert result.structural_signal == UNKNOWN
    assert result.background_interference == UNKNOWN
    assert 0.0 <= result.detectability_confidence <= 1.0


def test_detectability_all_unknown_when_characterization_is_empty():
    empty = MolecularCharacterizationResult(
        biomarker="X",
        dimension="mutation",
        molecular_characteristics=[],
        detectability=None,
        specificity_features=[],
        limitations=[],
        evidence=[],
        evidence_status=BiomarkerEvidenceStatus.INSUFFICIENT_EVIDENCE,
        evidence_status_reason="none",
    )
    service = MolecularDetectabilityService()

    result = service.assess(empty)

    assert result.abundance is None
    assert result.sequence_specificity == UNKNOWN
    assert result.chemical_distinguishability == UNKNOWN
    assert result.sample_compatibility == UNKNOWN
    assert result.detectability_confidence == 0.0


# --- detectability -> recognition ---------------------------------------------------


def test_recognition_consumes_detectability_without_bypassing_it():
    engine = MolecularRecognitionEngine()
    characterization = _characterization()
    detectability = MolecularDetectabilityService().assess(characterization)

    result = engine.recommend(characterization, graph_matches=[], detectability=detectability)

    dna = next(r for r in result if r.strategy == RecognitionStrategyType.DNA_HYBRIDIZATION)
    assert dna.status == "scored"


def test_recognition_not_yet_supported_strategies_cite_compatibility_table():
    engine = MolecularRecognitionEngine()
    result = engine.recommend(_characterization(), graph_matches=[])

    aptamer = next(r for r in result if r.strategy == RecognitionStrategyType.APTAMER)
    assert aptamer.status == "not_yet_supported"
    assert aptamer.compatibility_score is None  # stub protection: never fabricated


# --- recognition -> sensor (already downstream, confirm no bypass) ------------------


def test_compatibility_table_rows_carry_evidence_level_and_confidence():
    table = RecognitionCompatibilityTable()
    rules = table.all()
    assert len(rules) > 0
    for rule in rules:
        assert rule.evidence_level is not None
        assert rule.source
        assert rule.rationale
        assert 0.0 <= rule.confidence <= 1.0


# --- evidence provenance -------------------------------------------------------------


def test_evidence_ref_carries_provenance_fields_optionally():
    ref = EvidenceRef(
        source="NCI GDC",
        external_id="ENSG1",
        title="KRAS",
        dataset="GDC simple somatic mutation",
        access_level="open_with_citation",
        evidence_type="genomic_record",
    )
    assert ref.dataset == "GDC simple somatic mutation"
    # Backward-compat: old 3-arg construction still works.
    legacy = EvidenceRef(source="PubMed", external_id="pmid:1", title="Paper")
    assert legacy.dataset is None


# --- confidence calculation correctness + the critical regression guarantee ---------


def test_confidence_never_inflated_when_insufficient_evidence_recognition():
    engine = MolecularRecognitionEngine()
    empty_characterization = MolecularCharacterizationResult(
        biomarker="X",
        dimension="mutation",
        molecular_characteristics=[],
        detectability=None,
        specificity_features=[],
        limitations=[],
        evidence=[],
        evidence_status=BiomarkerEvidenceStatus.INSUFFICIENT_EVIDENCE,
        evidence_status_reason="none",
    )

    result = engine.recommend(empty_characterization, graph_matches=[])

    for rec in result:
        if rec.status == "insufficient_evidence":
            assert rec.confidence is None
            assert rec.compatibility_score is None


def test_confidence_never_inflated_when_insufficient_evidence_scoring():
    """The most important test in this task: INSUFFICIENT_EVIDENCE must never
    yield a high confidence or artificially inflated score anywhere in the
    R&D scoring composite.
    """
    service = RdScoringService()
    empty_characterization = MolecularCharacterizationResult(
        biomarker="X",
        dimension="mutation",
        molecular_characteristics=[],
        detectability=None,
        specificity_features=[],
        limitations=[],
        evidence=[],
        evidence_status=BiomarkerEvidenceStatus.INSUFFICIENT_EVIDENCE,
        evidence_status_reason="none",
    )

    result = service.score(
        biomarker_name="X",
        characterization=empty_characterization,
        recognition=None,
        sensor=None,
        priority_score=None,
    )

    for name, factor in result.components.items():
        assert factor.missing_data is True, f"{name} should be flagged missing_data"
        assert factor.score == 0.0, f"{name} score must not be inflated when evidence is missing"
    assert result.total_score == 0.0


def test_stub_recognition_strategies_never_produce_fabricated_scores():
    engine = MolecularRecognitionEngine()
    result = engine.recommend(_characterization(), graph_matches=[])

    for rec in result:
        if not rec.strategy.is_phase1_supported:
            assert rec.status == "not_yet_supported"
            assert rec.compatibility_score is None
            assert rec.confidence is None


# --- counterfactual scaffold ----------------------------------------------------------


def test_counterfactual_recognition_masks_one_evidence_source():
    engine = MolecularRecognitionEngine()
    characterization = _characterization(evidence_count=3)

    baseline = engine.recommend(characterization, graph_matches=[])
    counterfactual = engine.counterfactual_recommend(
        characterization, graph_matches=[], exclude_evidence_source="PubMed"
    )

    baseline_dna = next(r for r in baseline if r.strategy == RecognitionStrategyType.DNA_HYBRIDIZATION)
    cf_dna = next(r for r in counterfactual if r.strategy == RecognitionStrategyType.DNA_HYBRIDIZATION)
    # With PubMed evidence masked out, the heuristic score should not exceed baseline.
    assert (cf_dna.compatibility_score or 0) <= (baseline_dna.compatibility_score or 0)


# --- global data source role model ----------------------------------------------------


def test_data_sources_have_layer_role_and_access_level():
    for source in DATA_SOURCES:
        assert source.layer in ("population", "molecular", "evidence", "sensor")
        assert source.role
        assert source.access_level


def test_sources_for_layer_filters_correctly():
    molecular_sources = sources_for_layer("molecular")
    assert any(s.name == "NCI GDC" for s in molecular_sources)
    assert all(s.layer == "molecular" for s in molecular_sources)
