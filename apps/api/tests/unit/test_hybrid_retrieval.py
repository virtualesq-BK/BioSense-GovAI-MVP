from biosense.application.services.hybrid_retrieval_service import _map_literature_to_candidates
from biosense.domain.entities.literature import RetrievedChunk
from tests.unit.test_weighted_ranker import _sample_candidate


def test_literature_mapping_boosts_matching_sensor() -> None:
    candidate = _sample_candidate()
    chunks = [
        RetrievedChunk(
            chunk_id="c1",
            paper_id="p1",
            paper_external_id="pmid:123",
            paper_title="KRAS aptamer electrochemical",
            content="KRAS G12D mutation detected by electrochemical aptamer biosensor",
            score=0.85,
            chunk_index=0,
        )
    ]
    scores, citations = _map_literature_to_candidates([candidate], chunks)
    key = f"{candidate.sensor_id}:{candidate.recognition_id}"
    assert scores[key] > 0
    assert len(citations[key]) > 0
