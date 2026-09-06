from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from biosense.domain.entities.literature import RawPaperRecord
from biosense.infrastructure.external.pubmed_client import (
    DEFAULT_PUBMED_QUERIES,
    PubmedClient,
    _parse_pubmed_xml,
)

SAMPLE_ESEARCH = {
    "esearchresult": {
        "count": "1",
        "idlist": ["12345678"],
    }
}

SAMPLE_EFETCH_XML = """<?xml version="1.0"?>
<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2024//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/in.dtd">
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <Journal>
          <Title>Biosensors and Bioelectronics</Title>
          <JournalIssue>
            <PubDate>
              <Year>2024</Year>
              <Month>Mar</Month>
              <Day>15</Day>
            </PubDate>
          </JournalIssue>
        </Journal>
        <ArticleTitle>ctDNA electrochemical biosensor for early cancer detection</ArticleTitle>
        <Abstract>
          <AbstractText>We demonstrate a gold electrode aptamer sensor for KRAS ctDNA.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <LastName>Kim</LastName>
            <ForeName>Ji</ForeName>
          </Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
    <PubmedData>
      <ArticleIdList>
        <ArticleId IdType="doi">10.1000/example.doi</ArticleId>
        <ArticleId IdType="pubmed">12345678</ArticleId>
      </ArticleIdList>
    </PubmedData>
  </PubmedArticle>
</PubmedArticleSet>
"""


def test_default_queries_defined() -> None:
    assert len(DEFAULT_PUBMED_QUERIES) == 4
    assert "ctDNA AND biosensor AND cancer" in DEFAULT_PUBMED_QUERIES


def test_parse_pubmed_xml() -> None:
    records = _parse_pubmed_xml(SAMPLE_EFETCH_XML)
    assert len(records) == 1
    rec = records[0]
    assert rec.external_id == "pmid:12345678"
    assert "ctDNA" in rec.title
    assert "KRAS" in rec.abstract
    assert rec.journal == "Biosensors and Bioelectronics"
    assert rec.doi == "10.1000/example.doi"
    assert rec.published_at == date(2024, 3, 15)
    assert rec.authors == ["Ji Kim"]


@pytest.mark.asyncio
async def test_search_and_fetch_success() -> None:
    esearch_resp = MagicMock()
    esearch_resp.raise_for_status = MagicMock()
    esearch_resp.json.return_value = SAMPLE_ESEARCH

    efetch_resp = MagicMock()
    efetch_resp.raise_for_status = MagicMock()
    efetch_resp.text = SAMPLE_EFETCH_XML

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=[esearch_resp, efetch_resp])
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch(
            "biosense.infrastructure.external.pubmed_client.httpx.AsyncClient",
            return_value=mock_client,
        ),
        patch("biosense.infrastructure.external.pubmed_client.asyncio.sleep", new_callable=AsyncMock),
    ):
        client = PubmedClient()
        records = await client.search_and_fetch("ctDNA biosensor", max_results=5)

    assert len(records) == 1
    assert records[0].external_id == "pmid:12345678"
    assert mock_client.get.await_count == 2


@pytest.mark.asyncio
async def test_search_and_fetch_returns_empty_on_failure() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=ConnectionError("offline"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "biosense.infrastructure.external.pubmed_client.httpx.AsyncClient",
        return_value=mock_client,
    ):
        client = PubmedClient()
        records = await client.search_and_fetch("ctDNA", max_results=5)

    assert records == []


@pytest.mark.asyncio
async def test_harvest_default_deduplicates() -> None:
    paper = RawPaperRecord(
        external_id="pmid:1",
        title="T",
        abstract="A",
        journal=None,
        published_at=None,
        doi=None,
        authors=[],
    )
    client = PubmedClient()
    with (
        patch.object(client, "search_and_fetch", new_callable=AsyncMock, return_value=[paper]),
        patch("biosense.infrastructure.external.pubmed_client.asyncio.sleep", new_callable=AsyncMock),
    ):
        records = await client.harvest_default(max_results_per_query=2, queries=["q1", "q2"])

    assert len(records) == 1
