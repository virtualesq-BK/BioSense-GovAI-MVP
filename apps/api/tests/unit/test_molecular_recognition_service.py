from types import SimpleNamespace

from biosense.application.services.molecular_recognition_service import MolecularRecognitionEngine
from biosense.domain.entities.molecular_characterization import (
    Detectability,
    MolecularCharacterizationResult,
)
from biosense.domain.entities.biomarker_dimension import EvidenceRef
from biosense.domain.entities.molecular_recognition import RecognitionStrategyType


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
    )


def _match(code: str, score: float, mechanism: str = "curated mechanism"):
    return SimpleNamespace(
        recognition_strategy=SimpleNamespace(code=code),
        match_score=score,
        mechanism=mechanism,
    )


def test_non_phase1_strategies_are_not_yet_supported():
    engine = MolecularRecognitionEngine()
    result = engine.recommend(_characterization(), graph_matches=[])

    by_strategy = {r.strategy: r for r in result}
    for strategy in (
        RecognitionStrategyType.APTAMER,
        RecognitionStrategyType.ANTIBODY,
        RecognitionStrategyType.AFFINITY_BASED,
    ):
        rec = by_strategy[strategy]
        assert rec.status == "not_yet_supported"
        assert rec.compatibility_score is None


def test_phase1_strategy_uses_curated_graph_match_when_available():
    engine = MolecularRecognitionEngine()
    matches = [_match("dna_hybridization", 0.93)]

    result = engine.recommend(_characterization(), graph_matches=matches)
    dna = next(r for r in result if r.strategy == RecognitionStrategyType.DNA_HYBRIDIZATION)

    assert dna.status == "scored"
    assert dna.compatibility_score == 93.0
    assert dna.computation_basis["source"] == "biomarker_recognition_matches (domain graph)"


def test_phase1_strategy_falls_back_to_heuristic_without_curated_match():
    engine = MolecularRecognitionEngine()

    result = engine.recommend(_characterization(), graph_matches=[])
    crispr = next(r for r in result if r.strategy == RecognitionStrategyType.CRISPR_CAS)

    assert crispr.status == "scored"
    assert crispr.compatibility_score is not None
    assert crispr.compatibility_score <= 90.0
    assert crispr.confidence == 0.3
    assert "curated domain-graph compatibility record" in crispr.limitations[0]


def test_phase1_strategy_reports_insufficient_evidence_when_nothing_known():
    engine = MolecularRecognitionEngine()
    empty_characterization = MolecularCharacterizationResult(
        biomarker="X",
        dimension="mutation",
        molecular_characteristics=[],
        detectability=None,
        specificity_features=[],
        limitations=[],
        evidence=[],
    )

    result = engine.recommend(empty_characterization, graph_matches=[])
    dna = next(r for r in result if r.strategy == RecognitionStrategyType.DNA_HYBRIDIZATION)

    assert dna.status == "insufficient_evidence"
    assert dna.compatibility_score is None
