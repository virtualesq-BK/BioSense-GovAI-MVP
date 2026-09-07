from types import SimpleNamespace

from biosense.application.services.sensor_transduction_service import SensorTransductionEngine
from biosense.domain.entities.molecular_recognition import (
    RecognitionRecommendation,
    RecognitionStrategyType,
)
from biosense.domain.entities.sensor_transduction import SensorPlatformType


def _scored_recognition(score=80.0):
    return RecognitionRecommendation(
        strategy=RecognitionStrategyType.DNA_HYBRIDIZATION,
        status="scored",
        compatibility_score=score,
        rationale="test",
        supporting_evidence=["PubMed:pmid:1 — A paper"],
        limitations=[],
        confidence=0.7,
    )


def _sensor_use(efficiency=0.9, with_performance=True):
    performance = None
    if with_performance:
        performance = SimpleNamespace(
            sensitivity=0.94, specificity=0.96, lod_value=0.001, lod_unit="ng/mL", is_estimated=True
        )
    sensor = SimpleNamespace(
        name="AI-Electrochemical Biosensor",
        sensor_type="electrochemical",
        performances=[performance] if performance else [],
    )
    return SimpleNamespace(efficiency=efficiency, sensor=sensor)


def test_non_electrochemical_platforms_not_yet_implemented():
    engine = SensorTransductionEngine()
    result = engine.transduce(_scored_recognition(), sensor_uses=[])

    by_platform = {c.platform: c for c in result}
    for platform in (
        SensorPlatformType.OPTICAL,
        SensorPlatformType.SERS,
        SensorPlatformType.SPR,
        SensorPlatformType.FLUORESCENCE,
        SensorPlatformType.OTHER,
    ):
        candidate = by_platform[platform]
        assert candidate.status == "not_yet_implemented"
        assert candidate.feasibility_score is None


def test_electrochemical_scored_with_real_sensor_use_and_performance():
    engine = SensorTransductionEngine()
    uses = [_sensor_use()]

    result = engine.transduce(_scored_recognition(), sensor_uses=uses)
    ec = next(c for c in result if c.platform == SensorPlatformType.ELECTROCHEMICAL)

    assert ec.status == "scored"
    assert ec.sensor_name == "AI-Electrochemical Biosensor"
    assert ec.feasibility_score is not None
    assert ec.sensitivity == 0.94
    assert ec.is_estimated is True


def test_electrochemical_insufficient_evidence_without_sensor_uses():
    engine = SensorTransductionEngine()

    result = engine.transduce(_scored_recognition(), sensor_uses=[])
    ec = next(c for c in result if c.platform == SensorPlatformType.ELECTROCHEMICAL)

    assert ec.status == "insufficient_evidence"
    assert ec.feasibility_score is None


def test_electrochemical_insufficient_evidence_when_recognition_not_scored():
    engine = SensorTransductionEngine()
    unscored = RecognitionRecommendation(
        strategy=RecognitionStrategyType.CRISPR_CAS,
        status="insufficient_evidence",
        compatibility_score=None,
        rationale="test",
    )

    result = engine.transduce(unscored, sensor_uses=[_sensor_use()])
    ec = next(c for c in result if c.platform == SensorPlatformType.ELECTROCHEMICAL)

    assert ec.status == "insufficient_evidence"
