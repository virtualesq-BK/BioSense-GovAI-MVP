from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from biosense.api.main import app


@pytest.mark.asyncio
async def test_ingest_text_endpoint() -> None:
    with patch(
        "biosense.api.v1.literature.LiteratureIngestionPipeline.ingest_text",
        new_callable=AsyncMock,
    ) as mock_ingest:
        from datetime import datetime
        from uuid import uuid4

        paper_id = uuid4()

        class FakePaper:
            id = paper_id
            external_id = "pmid:test"
            title = "Test Paper"
            source = "text"
            ingestion_status = "indexed"
            chunk_count = 3
            pdf_filename = None
            created_at = datetime.now()

        mock_ingest.return_value = paper_id

        with patch(
            "biosense.api.v1.literature.LiteratureRepository.get_paper",
            new_callable=AsyncMock,
            return_value=FakePaper(),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/v1/literature/papers/ingest-text",
                    json={
                        "external_id": "pmid:test",
                        "title": "Test Paper",
                        "text": "KRAS ctDNA electrochemical biosensor " * 20,
                    },
                )

    assert response.status_code == 200
    assert response.json()["ingestion_status"] == "indexed"


@pytest.mark.asyncio
async def test_rag_query_endpoint() -> None:
    mock_result = {
        "query": "KRAS biosensor",
        "cancer_type": None,
        "biomarker_name": "KRAS",
        "recommendations": [
            {
                "biomarker_name": "KRAS G12D",
                "sensor_strategy": "electrochemical",
                "recognition_approach": "aptamer-based",
                "rationale": "Literature evidence",
                "confidence": 0.9,
                "citations": [],
            }
        ],
        "citations": [],
        "chunks_retrieved": 2,
        "latency_ms": 50,
    }
    with patch(
        "biosense.api.v1.literature.LiteratureRagQueryService.query",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/literature/rag/query",
                json={"query": "KRAS biosensor", "biomarker_name": "KRAS"},
            )

    assert response.status_code == 200
    body = response.json()
    assert len(body["recommendations"]) == 1
    assert body["chunks_retrieved"] == 2


@pytest.mark.asyncio
async def test_ingestion_status_endpoint() -> None:
    with patch(
        "biosense.api.v1.literature.LiteratureRepository.get_ingestion_stats",
        new_callable=AsyncMock,
        return_value={
            "total_papers": 5,
            "indexed_papers": 4,
            "pending_papers": 1,
            "failed_papers": 0,
            "total_chunks": 20,
        },
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/v1/literature/ingestion/status")

    assert response.status_code == 200
    assert response.json()["indexed_papers"] == 4
