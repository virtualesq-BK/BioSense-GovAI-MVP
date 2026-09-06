"""NCBI PubMed E-utilities client (esearch + efetch)."""

from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from datetime import date

import httpx
import structlog

from biosense.config import settings
from biosense.domain.entities.literature import RawPaperRecord
from biosense.infrastructure.common.retry import with_retry

logger = structlog.get_logger()

DEFAULT_PUBMED_QUERIES: tuple[str, ...] = (
    "ctDNA AND biosensor AND cancer",
    "exosome miRNA cancer diagnosis",
    "SERS cancer biomarker liquid biopsy",
    "liquid biopsy early cancer detection AI",
)


class PubmedClient:
    """PubMed search + fetch via NCBI E-utilities."""

    SOURCE = "pubmed"

    def __init__(self) -> None:
        self._base = settings.pubmed_base_url.rstrip("/")

    async def search_and_fetch(
        self, query: str, *, max_results: int = 20
    ) -> list[RawPaperRecord]:
        async def _call() -> list[RawPaperRecord]:
            pmids = await self._esearch(query, max_results=max_results)
            if not pmids:
                return []
            # Free tier: ~3 req/s; with API key: ~10 req/s
            await asyncio.sleep(0.34 if not settings.pubmed_api_key else 0.11)
            return await self._efetch(pmids)

        try:
            return await with_retry(_call, operation_name="pubmed_search_fetch")
        except Exception as exc:
            logger.error("pubmed_fetch_failed", query=query, error=str(exc))
            return []

    async def harvest_default(
        self, *, max_results_per_query: int = 20, queries: list[str] | None = None
    ) -> list[RawPaperRecord]:
        terms = queries or list(DEFAULT_PUBMED_QUERIES)
        seen: set[str] = set()
        records: list[RawPaperRecord] = []
        for term in terms:
            batch = await self.search_and_fetch(term, max_results=max_results_per_query)
            for rec in batch:
                if rec.external_id in seen:
                    continue
                seen.add(rec.external_id)
                records.append(rec)
            await asyncio.sleep(0.34 if not settings.pubmed_api_key else 0.11)
        logger.info("pubmed_harvest_complete", queries=len(terms), papers=len(records))
        return records

    async def _esearch(self, query: str, *, max_results: int) -> list[str]:
        params: dict[str, str | int] = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
        }
        if settings.pubmed_api_key:
            params["api_key"] = settings.pubmed_api_key

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self._base}/esearch.fcgi", params=params)
            response.raise_for_status()
            payload = response.json()

        result = payload.get("esearchresult", {})
        id_list = result.get("idlist") or []
        if not isinstance(id_list, list):
            raise ValueError("PubMed esearch returned invalid idlist")
        return [str(pmid) for pmid in id_list if pmid]

    async def _efetch(self, pmids: list[str]) -> list[RawPaperRecord]:
        params: dict[str, str] = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }
        if settings.pubmed_api_key:
            params["api_key"] = settings.pubmed_api_key

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{self._base}/efetch.fcgi", params=params)
            response.raise_for_status()
            xml_text = response.text

        if not xml_text.strip():
            raise ValueError("PubMed efetch returned empty body")

        return _parse_pubmed_xml(xml_text)


def _parse_pubmed_xml(xml_text: str) -> list[RawPaperRecord]:
    root = ET.fromstring(xml_text)
    records: list[RawPaperRecord] = []
    for article in root.findall(".//PubmedArticle"):
        pmid_el = article.find("./MedlineCitation/PMID")
        if pmid_el is None or not (pmid_el.text or "").strip():
            continue
        pmid = pmid_el.text.strip()

        title_el = article.find("./MedlineCitation/Article/ArticleTitle")
        title = "".join(title_el.itertext()).strip() if title_el is not None else ""
        if not title:
            continue

        abstract_parts = [
            "".join(ab.itertext()).strip()
            for ab in article.findall("./MedlineCitation/Article/Abstract/AbstractText")
        ]
        abstract = "\n".join(p for p in abstract_parts if p)

        journal_el = article.find("./MedlineCitation/Article/Journal/Title")
        journal = (journal_el.text or "").strip() if journal_el is not None else None

        authors = _extract_authors(article)
        published = _extract_published_date(article)
        doi = _extract_doi(article)

        records.append(
            RawPaperRecord(
                external_id=f"pmid:{pmid}",
                title=title,
                abstract=abstract,
                journal=journal or None,
                published_at=published,
                doi=doi,
                authors=authors,
            )
        )
    return records


def _extract_authors(article: ET.Element) -> list[str]:
    names: list[str] = []
    for author in article.findall("./MedlineCitation/Article/AuthorList/Author"):
        last = author.findtext("LastName") or ""
        fore = author.findtext("ForeName") or author.findtext("Initials") or ""
        collective = author.findtext("CollectiveName")
        if collective:
            names.append(collective.strip())
        elif last:
            names.append(f"{fore} {last}".strip())
    return names


def _extract_published_date(article: ET.Element) -> date | None:
    for path in (
        "./MedlineCitation/Article/Journal/JournalIssue/PubDate",
        "./MedlineCitation/Article/ArticleDate",
        "./PubmedData/History/PubMedPubDate[@PubStatus='pubmed']",
    ):
        node = article.find(path)
        if node is None:
            continue
        year = node.findtext("Year")
        month = node.findtext("Month") or "1"
        day = node.findtext("Day") or "1"
        if not year:
            medline = node.findtext("MedlineDate")
            if medline and len(medline) >= 4 and medline[:4].isdigit():
                year = medline[:4]
            else:
                continue
        try:
            month_num = int(month) if month.isdigit() else _month_name_to_num(month)
            return date(int(year), month_num, int(day) if str(day).isdigit() else 1)
        except ValueError:
            continue
    return None


def _month_name_to_num(name: str) -> int:
    mapping = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "dec": 12,
    }
    return mapping.get(name[:3].lower(), 1)


def _extract_doi(article: ET.Element) -> str | None:
    for el in article.findall("./PubmedData/ArticleIdList/ArticleId"):
        if el.get("IdType") == "doi" and el.text:
            return el.text.strip()
    return None
