from biosense.domain.entities.recommendation import GraphCandidate
from biosense.domain.services.weighted_ranker import ConfidenceScorer, WeightedRanker


def _sample_candidate(**overrides) -> GraphCandidate:
    base = dict(
        biomarker_id="b1",
        biomarker_name="KRAS G12D mutation",
        recognition_id="r1",
        recognition_code="aptamer_based",
        recognition_name="Anti-KRAS aptamer",
        sensor_id="s1",
        sensor_name="Gold electrode EC sensor",
        sensor_type="electrochemical",
        match_score=0.92,
        sensor_efficiency=0.88,
        sensitivity=0.92,
        specificity=0.94,
        lod_value=0.1,
        lod_unit="ng/mL",
        estimated_cost_usd=35.0,
        protocol_steps=["Step 1", "Step 2"],
        graph_path="Cancer→KRAS→aptamer→electrochemical",
    )
    base.update(overrides)
    return GraphCandidate(**base)


def test_weighted_ranker_orders_by_composite_score() -> None:
    ranker = WeightedRanker()
    high = _sample_candidate(match_score=0.95, sensor_efficiency=0.9)
    low = _sample_candidate(
        sensor_id="s2",
        sensor_type="lateral_flow",
        match_score=0.6,
        sensor_efficiency=0.5,
    )
    ranked = ranker.rank([low, high], literature_scores={}, public_health_score=0.7)
    assert ranked[0].candidate.sensor_type == "electrochemical"
    assert ranked[0].composite_score > ranked[1].composite_score


def test_literature_boost_increases_score() -> None:
    ranker = WeightedRanker()
    candidate = _sample_candidate()
    key = f"{candidate.sensor_id}:{candidate.recognition_id}"
    without = ranker.rank([candidate], {}, 0.5)[0].composite_score
    with_lit = ranker.rank([candidate], {key: 0.9}, 0.5)[0].composite_score
    assert with_lit > without


def test_confidence_scorer_bounded() -> None:
    candidate = _sample_candidate()
    conf = ConfidenceScorer.compute(candidate, literature_score=0.8, composite_score=0.85)
    assert 0.0 <= conf <= 1.0
