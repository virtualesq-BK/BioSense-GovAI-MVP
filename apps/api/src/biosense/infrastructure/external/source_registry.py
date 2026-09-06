"""Static registry of every external data source this platform actually integrates.

Pure data, no I/O — mirrors docs/data-access.md. Kept in one place so `/v1/sources`
never drifts from what's really wired up (only sources with a working connector or
explicit external-reference-only listing appear here — nothing aspirational).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataSourceInfo:
    name: str
    provider: str
    source_type: str  # "government" | "genomic" | "literature"
    access_method: str  # "api" | "external_reference"
    license: str
    update_method: str
    url: str


DATA_SOURCES: tuple[DataSourceInfo, ...] = (
    DataSourceInfo(
        name="KOSIS",
        provider="Statistics Korea",
        source_type="government",
        access_method="api",
        license="Korea Open Government License (KOGL)",
        update_method="On-demand API call, cached; falls back to seed data if unavailable",
        url="https://kosis.kr/openapi/",
    ),
    DataSourceInfo(
        name="KDCA",
        provider="Korea Disease Control and Prevention Agency",
        source_type="government",
        access_method="api",
        license="Public data terms of use (data.go.kr)",
        update_method="On-demand API call, cached; falls back to seed data if unavailable",
        url="https://health.kdca.go.kr/",
    ),
    DataSourceInfo(
        name="NCI GDC",
        provider="National Cancer Institute (NIH)",
        source_type="genomic",
        access_method="api",
        license="Open-access tier: free use with citation; controlled-access requires "
        "separate dbGaP authorization (not integrated)",
        update_method="Live query per request (no local caching of GDC data)",
        url="https://gdc.cancer.gov/",
    ),
    DataSourceInfo(
        name="PubMed",
        provider="NCBI / National Library of Medicine",
        source_type="literature",
        access_method="api",
        license="Public domain / NLM terms of use",
        update_method="Scheduled + on-demand harvest via E-utilities",
        url="https://pubmed.ncbi.nlm.nih.gov/",
    ),
    DataSourceInfo(
        name="Europe PMC",
        provider="EMBL-EBI",
        source_type="literature",
        access_method="api",
        license="Source-dependent; EBI Privacy Notice governs API use",
        update_method="On-demand harvest via REST API",
        url="https://europepmc.org/",
    ),
    DataSourceInfo(
        name="CDC USCS (United States Cancer Statistics)",
        provider="CDC / NCI",
        source_type="government",
        access_method="external_reference",
        license="Public, subject to CDC WONDER data-use restrictions",
        update_method="Not integrated — no automatable API exists (see docs/data-access.md); "
        "linked as an external reference only",
        url="https://wonder.cdc.gov/cancer-v2022.html",
    ),
)
