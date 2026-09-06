"""Unit tests for regex/rule-based metric extraction from paper sentences."""

from uuid import uuid4

from biosense.application.services.metric_extraction_service import (
    find_metric_candidate_sentences,
    parse_llm_metrics_json,
    parse_metric_from_sentence,
    resolve_sensor_id,
)


def test_extract_sensitivity_and_specificity() -> None:
    sentence = (
        "The electrochemical biosensor showed a sensitivity of 94.5% and "
        "specificity of 91.2% for KRAS G12D ctDNA detection."
    )
    metric = parse_metric_from_sentence(sentence)
    assert metric.sensitivity == 0.945
    assert metric.specificity == 0.912
    assert metric.is_estimated is False
    assert metric.sensor_type_hint == "electrochemical"


def test_extract_auc() -> None:
    sentence = (
        "ROC analysis yielded an AUC = 0.93 for the optical SPR assay "
        "across 120 clinical plasma samples."
    )
    metric = parse_metric_from_sentence(sentence)
    assert metric.auc == 0.93
    assert metric.sensor_type_hint == "optical"


def test_extract_lod_with_unit() -> None:
    sentence = (
        "The limit of detection (LOD) of 0.05 ng/mL was achieved using "
        "a graphene FET sensor platform."
    )
    metric = parse_metric_from_sentence(sentence)
    assert metric.lod_value == 0.05
    assert metric.lod_unit == "ng/mL"
    assert metric.sensor_type_hint == "fet"


def test_extract_assay_time_and_sample_volume() -> None:
    sentence = (
        "The microfluidic assay time was 25 minutes using 50 µL of plasma "
        "with a lateral flow readout cartridge."
    )
    metric = parse_metric_from_sentence(sentence)
    assert metric.assay_time_minutes == 25.0
    assert metric.sample_volume == 50.0
    assert metric.sample_volume_unit == "µL"


def test_extract_assay_time_hours_to_minutes() -> None:
    sentence = (
        "Detection was completed within 2 hours using an electrochemical "
        "impedance spectroscopy workflow for ctDNA."
    )
    metric = parse_metric_from_sentence(sentence)
    assert metric.assay_time_minutes == 120.0


def test_extract_cost_usd() -> None:
    sentence = (
        "The estimated cost of the lateral flow assay was $12.50 per test "
        "including reagents and the disposable strip."
    )
    metric = parse_metric_from_sentence(sentence)
    assert metric.estimated_cost_usd == 12.5
    assert metric.sensor_type_hint == "lateral_flow"


def test_find_metric_candidate_sentences_filters_noise() -> None:
    chunks = [
        "Introduction. Cancer remains a leading cause of mortality worldwide.",
        "Results. The sensor achieved sensitivity of 88% in blinded validation.",
        "Methods. Samples were stored at -80C until analysis.",
        "LOD of 2.5 pM was reported for the aptamer assay.",
    ]
    candidates = find_metric_candidate_sentences(chunks)
    assert len(candidates) >= 2
    assert any("sensitivity of 88%" in c for c in candidates)
    assert any("LOD of 2.5 pM" in c for c in candidates)
    assert all("leading cause of mortality" not in c for c in candidates)


def test_parse_llm_metrics_json() -> None:
    raw = """{
      "metrics": [{
        "sensitivity": 0.9,
        "specificity": 0.85,
        "auc": 0.91,
        "lod_value": 1.2,
        "lod_unit": "ng/mL",
        "assay_time_minutes": 30,
        "sample_volume": 100,
        "sample_volume_unit": "µL",
        "estimated_cost_usd": 20,
        "sensor_type_hint": "electrochemical",
        "extraction_confidence": 0.8,
        "source_excerpt": "sensitivity 90%"
      }]
    }"""
    metrics = parse_llm_metrics_json(raw)
    assert len(metrics) == 1
    assert metrics[0].sensitivity == 0.9
    assert metrics[0].lod_unit == "ng/mL"
    assert metrics[0].extraction_confidence == 0.8


def test_resolve_sensor_id_by_type_hint() -> None:
    sensors = [
        {"id": uuid4(), "name": "Gold electrode", "sensor_type": "electrochemical"},
        {"id": uuid4(), "name": "SPR chip", "sensor_type": "optical"},
    ]
    metric = parse_metric_from_sentence(
        "Electrochemical sensor sensitivity of 92% for ctDNA in plasma samples."
    )
    resolved = resolve_sensor_id(metric, sensors, metric.source_excerpt)
    assert resolved == sensors[0]["id"]
