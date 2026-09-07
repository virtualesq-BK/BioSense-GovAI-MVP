"""NCI Genomic Data Commons (GDC) REST API client.

GDC (https://api.gdc.cancer.gov) is a genuine, public, open-access REST API —
verified live (2026-09-07): /projects, /genes, /ssms, /status all respond
without authentication for open-access metadata. See docs/data-access.md.

Only open-access, high-level data is used here (project/gene/mutation-level
metadata). Controlled-access data (raw sequencing files, germline variants)
is out of scope for this client by design — see project rule against
bypassing controlled-access restrictions.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import structlog

from biosense.config import settings
from biosense.domain.entities.genomics import (
    RawGdcGeneRecord,
    RawGdcMethylationFileRecord,
    RawGdcMutationRecord,
    RawGdcProjectRecord,
)
from biosense.domain.services.normalization import normalize_gene_symbol
from biosense.infrastructure.common.retry import with_retry
from biosense.infrastructure.external.base import PublicDataConnector

logger = structlog.get_logger()

GdcRecord = RawGdcProjectRecord | RawGdcGeneRecord | RawGdcMutationRecord


class GdcClient(PublicDataConnector):
    """Search + fetch open-access GDC metadata (projects, genes, mutations)."""

    SOURCE = "gdc"

    def __init__(self) -> None:
        self._base = settings.gdc_api_url.rstrip("/")

    async def search(
        self, query: str, filters: dict[str, Any] | None = None
    ) -> list[GdcRecord]:
        """Search GDC. `filters["entity"]` selects "projects" (default), "genes",
        or "mutations"; `query` is used as the primary_site / symbol / gene_symbol
        value for that entity."""
        entity = (filters or {}).get("entity", "projects")
        if entity == "genes":
            return list(await self.search_genes(query))
        if entity == "mutations":
            return list(await self.search_mutations(gene_symbol=query or None))
        return list(await self.search_projects(primary_site=query or None))

    async def fetch(self, identifier: str) -> RawGdcProjectRecord | None:
        """Fetch a single project by its GDC project_id (e.g. 'TCGA-LUAD')."""
        filters = {"op": "in", "content": {"field": "project_id", "value": [identifier]}}

        async def _call() -> RawGdcProjectRecord | None:
            payload = await self._get(
                "projects",
                fields="project_id,name,primary_site,disease_type,summary.case_count",
                filters=filters,
                size=1,
            )
            return _parse_project(payload[0]) if payload else None

        try:
            return await with_retry(_call, operation_name="gdc_fetch_project")
        except Exception as exc:
            logger.error("gdc_fetch_project_failed", identifier=identifier, error=str(exc))
            return None

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self._base}/status")
                response.raise_for_status()
                payload = response.json()
            return payload.get("status") == "OK"
        except Exception as exc:
            logger.warning("gdc_health_check_failed", error=str(exc))
            return False

    async def search_projects(
        self, *, primary_site: str | None = None, size: int = 20
    ) -> list[RawGdcProjectRecord]:
        """Search GDC projects (e.g. TCGA cohorts), optionally filtered by primary site."""

        filters = None
        if primary_site:
            filters = {
                "op": "in",
                "content": {"field": "primary_site", "value": [primary_site]},
            }

        async def _call() -> list[RawGdcProjectRecord]:
            payload = await self._get(
                "projects",
                fields="project_id,name,primary_site,disease_type,summary.case_count",
                filters=filters,
                size=size,
            )
            return [_parse_project(hit) for hit in payload]

        try:
            return await with_retry(_call, operation_name="gdc_search_projects")
        except Exception as exc:
            logger.error("gdc_search_projects_failed", error=str(exc))
            return []

    async def search_genes(self, symbol: str, *, size: int = 5) -> list[RawGdcGeneRecord]:
        """Look up gene annotations by HGNC symbol (e.g. 'KRAS')."""

        filters = {
            "op": "in",
            "content": {"field": "symbol", "value": [normalize_gene_symbol(symbol)]},
        }

        async def _call() -> list[RawGdcGeneRecord]:
            payload = await self._get(
                "genes",
                fields="gene_id,symbol,name,biotype",
                filters=filters,
                size=size,
            )
            return [_parse_gene(hit) for hit in payload]

        try:
            return await with_retry(_call, operation_name="gdc_search_genes")
        except Exception as exc:
            logger.error("gdc_search_genes_failed", symbol=symbol, error=str(exc))
            return []

    async def search_mutations(
        self, *, gene_symbol: str | None = None, size: int = 20
    ) -> list[RawGdcMutationRecord]:
        """Search simple somatic mutations (SSMs), optionally filtered by gene symbol."""

        filters = None
        if gene_symbol:
            filters = {
                "op": "in",
                "content": {
                    "field": "consequence.transcript.gene.symbol",
                    "value": [normalize_gene_symbol(gene_symbol)],
                },
            }

        async def _call() -> list[RawGdcMutationRecord]:
            payload = await self._get(
                "ssms",
                fields=(
                    "ssm_id,genomic_dna_change,mutation_subtype,"
                    "consequence.transcript.gene.symbol,consequence.transcript.aa_change"
                ),
                filters=filters,
                size=size,
            )
            return [_parse_mutation(hit) for hit in payload]

        try:
            return await with_retry(_call, operation_name="gdc_search_mutations")
        except Exception as exc:
            logger.error("gdc_search_mutations_failed", gene_symbol=gene_symbol, error=str(exc))
            return []

    async def search_methylation_files(
        self, *, project_id: str, size: int = 20
    ) -> list[RawGdcMethylationFileRecord]:
        """FILE-LEVEL methylation array discovery via GET /files (metadata only).

        Per the Phase 2 Step 0 audit (docs/data-feasibility-phase2.md), the GDC
        REST API exposes only file/platform/case-level metadata for methylation
        — file_id, data_type, platform, access, case/project linkage. There is
        no field for actual CpG-site IDs or beta values via this endpoint; those
        require downloading/parsing TXT/IDAT files offline, which is explicitly
        out of scope here. Never populate a quantitative value from this method.
        """
        filters = {
            "op": "and",
            "content": [
                {
                    "op": "in",
                    "content": {"field": "cases.project.project_id", "value": [project_id]},
                },
                {
                    "op": "in",
                    "content": {"field": "data_type", "value": ["Methylation Beta Value"]},
                },
            ],
        }

        async def _call() -> list[RawGdcMethylationFileRecord]:
            payload = await self._get(
                "files",
                fields=(
                    "file_id,file_name,data_type,platform,access,"
                    "cases.project.project_id,cases.samples.sample_type"
                ),
                filters=filters,
                size=size,
            )
            return [_parse_methylation_file(hit) for hit in payload]

        try:
            return await with_retry(_call, operation_name="gdc_search_methylation_files")
        except Exception as exc:
            logger.error(
                "gdc_search_methylation_files_failed", project_id=project_id, error=str(exc)
            )
            return []

    async def count_mutations_for_gene(self, gene_symbol: str) -> int | None:
        """Total number of recorded SSMs for a gene (not capped by page size).

        Returns None on failure — callers must treat that as "unknown", not zero.
        """
        filters = {
            "op": "in",
            "content": {
                "field": "consequence.transcript.gene.symbol",
                "value": [normalize_gene_symbol(gene_symbol)],
            },
        }

        async def _call() -> int:
            return await self._count("ssms", filters=filters)

        try:
            return await with_retry(_call, operation_name="gdc_count_mutations")
        except Exception as exc:
            logger.error("gdc_count_mutations_failed", gene_symbol=gene_symbol, error=str(exc))
            return None

    async def _count(self, endpoint: str, *, filters: dict) -> int:
        params: dict[str, str | int] = {"size": 0, "format": "JSON", "filters": json.dumps(filters)}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self._base}/{endpoint}", params=params)
            response.raise_for_status()
            payload = response.json()
        total = payload.get("data", {}).get("pagination", {}).get("total")
        if not isinstance(total, int):
            raise ValueError(f"GDC {endpoint} count returned no pagination.total")
        return total

    async def _get(
        self,
        endpoint: str,
        *,
        fields: str,
        size: int,
        filters: dict | None = None,
    ) -> list[dict]:
        params: dict[str, str | int] = {"fields": fields, "size": size, "format": "JSON"}
        if filters is not None:
            params["filters"] = json.dumps(filters)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self._base}/{endpoint}", params=params)
            response.raise_for_status()
            payload = response.json()

        hits = payload.get("data", {}).get("hits")
        if not isinstance(hits, list):
            raise ValueError(f"GDC {endpoint} returned no hits array")
        return hits


def _parse_project(hit: dict) -> RawGdcProjectRecord:
    summary = hit.get("summary") or {}
    return RawGdcProjectRecord(
        project_id=hit.get("project_id") or hit.get("id", ""),
        name=hit.get("name", ""),
        primary_sites=list(hit.get("primary_site") or []),
        disease_types=list(hit.get("disease_type") or []),
        case_count=summary.get("case_count"),
        source=GdcClient.SOURCE,
    )


def _parse_gene(hit: dict) -> RawGdcGeneRecord:
    return RawGdcGeneRecord(
        gene_id=hit.get("gene_id") or hit.get("id", ""),
        symbol=hit.get("symbol", ""),
        name=hit.get("name"),
        biotype=hit.get("biotype"),
        source=GdcClient.SOURCE,
    )


def _parse_mutation(hit: dict) -> RawGdcMutationRecord:
    gene_symbols: list[str] = []
    aa_changes: list[str] = []
    for consequence in hit.get("consequence") or []:
        transcript = consequence.get("transcript") or {}
        gene = transcript.get("gene") or {}
        symbol = gene.get("symbol")
        if symbol and symbol not in gene_symbols:
            gene_symbols.append(symbol)
        aa_change = transcript.get("aa_change")
        if aa_change and aa_change not in aa_changes:
            aa_changes.append(aa_change)

    return RawGdcMutationRecord(
        ssm_id=hit.get("ssm_id") or hit.get("id", ""),
        genomic_dna_change=hit.get("genomic_dna_change"),
        mutation_subtype=hit.get("mutation_subtype"),
        gene_symbols=gene_symbols,
        amino_acid_changes=aa_changes,
        source=GdcClient.SOURCE,
    )


def _parse_methylation_file(hit: dict) -> RawGdcMethylationFileRecord:
    project_id: str | None = None
    sample_types: list[str] = []
    case_count = 0
    for case in hit.get("cases") or []:
        case_count += 1
        project = case.get("project") or {}
        if project.get("project_id") and project_id is None:
            project_id = project.get("project_id")
        for sample in case.get("samples") or []:
            st = sample.get("sample_type")
            if st and st not in sample_types:
                sample_types.append(st)

    return RawGdcMethylationFileRecord(
        file_id=hit.get("file_id") or hit.get("id", ""),
        file_name=hit.get("file_name"),
        data_type=hit.get("data_type"),
        platform=hit.get("platform"),
        access=hit.get("access"),
        project_id=project_id,
        case_count=case_count or None,
        sample_types=sample_types,
        source=GdcClient.SOURCE,
    )
