from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from biosense.application.services.pubmed_harvest_service import PubmedHarvestService
from biosense.domain.entities.literature import RawPaperRecord


@pytest.mark.asyncio
async def test_harvest_service_ingests_new_papers() -> None:
    paper_id = uuid4()
    record = RawPaperRecord(
        external_id="pmid:99",
        title="SERS liquid biopsy",
        abstract="Early cancer detection with SERS.",
        journal="Nature",
        published_at=date(2023, 1, 1),
        doi="10.1/x",
        authors=["A Author"],
    )

    pubmed = MagicMock()
    pubmed.harvest_default = AsyncMock(return_value=[record])

    pipeline = MagicMock()
    pipeline.ingest_text = AsyncMock(return_value=paper_id)

    session = MagicMock()
    service = PubmedHarvestService(session, pubmed=pubmed, pipeline=pipeline)
    # Patch repo used inside service after init
    service._repo.get_paper_by_external_id = AsyncMock(return_value=None)

    result = await service.harvest(queries=["SERS cancer"], max_results_per_query=5)

    assert result["harvested"] == 1
    assert result["skipped"] == 0
    assert result["failed"] == 0
    assert result["paper_ids"] == [str(paper_id)]
    pipeline.ingest_text.assert_awaited_once()
    call_kwargs = pipeline.ingest_text.await_args.kwargs
    assert call_kwargs["external_id"] == "pmid:99"
    assert call_kwargs["source"] == "pubmed"


@pytest.mark.asyncio
async def test_harvest_service_skips_empty_abstract() -> None:
    record = RawPaperRecord(
        external_id="pmid:1",
        title="No abstract",
        abstract="   ",
        journal=None,
        published_at=None,
        doi=None,
        authors=[],
    )
    pubmed = MagicMock()
    pubmed.harvest_default = AsyncMock(return_value=[record])
    pipeline = MagicMock()
    pipeline.ingest_text = AsyncMock()

    service = PubmedHarvestService(MagicMock(), pubmed=pubmed, pipeline=pipeline)
    service._repo.get_paper_by_external_id = AsyncMock(return_value=None)

    result = await service.harvest(queries=["q"])

    assert result["skipped"] == 1
    assert result["harvested"] == 0
    pipeline.ingest_text.assert_not_called()
