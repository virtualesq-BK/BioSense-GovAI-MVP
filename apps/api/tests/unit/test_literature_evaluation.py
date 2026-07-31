from biosense.application.services.literature_rag_service import _compute_metrics
from biosense.domain.entities.literature import RetrievedChunk


def test_compute_metrics_precision_and_mrr() -> None:
    chunks = [
        RetrievedChunk("c1", "p1", "pmid:1", "Title 1", "KRAS mutation in ctDNA", 0.9, 0),
        RetrievedChunk("c2", "p2", "pmid:2", "Title 2", "unrelated cardiovascular", 0.7, 1),
        RetrievedChunk("c3", "p3", "pmid:3", "Title 3", "aptamer biosensor design", 0.6, 0),
    ]
    result = _compute_metrics(chunks, ["KRAS", "aptamer"], top_k=3)
    assert abs(result["precision_at_k"] - 2 / 3) < 0.01
    assert result["mrr"] == 1.0
    assert result["chunks_evaluated"] == 3


def test_compute_metrics_empty_chunks() -> None:
    result = _compute_metrics([], ["KRAS"], top_k=5)
    assert result["precision_at_k"] == 0.0
    assert result["mrr"] == 0.0
