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
    # Additive (Phase 1.5) role-model fields — optional/defaulted so this
    # stays backward compatible with any existing consumer of DATA_SOURCES.
    layer: str | None = None  # "population" | "molecular" | "evidence" | "sensor"
    role: str | None = None  # what this source is used for in the pipeline
    access_level: str | None = None  # "public" | "open_with_citation" | "controlled_access"


DATA_SOURCES: tuple[DataSourceInfo, ...] = (
    DataSourceInfo(
        name="KOSIS",
        provider="Statistics Korea",
        source_type="government",
        access_method="api",
        license="Korea Open Government License (KOGL)",
        update_method="On-demand API call, cached; falls back to seed data if unavailable",
        url="https://kosis.kr/openapi/",
        layer="population",
        role="National/regional population and demographic denominators for incidence/mortality rates.",
        access_level="public",
    ),
    DataSourceInfo(
        name="KDCA",
        provider="Korea Disease Control and Prevention Agency",
        source_type="government",
        access_method="api",
        license="Public data terms of use (data.go.kr)",
        update_method="On-demand API call, cached; falls back to seed data if unavailable",
        url="https://health.kdca.go.kr/",
        layer="population",
        role="Regional/national cancer incidence and mortality statistics (epidemiological evidence layer).",
        access_level="public",
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
        layer="molecular",
        role="Gene/mutation records and mutation counts used by Molecular Characterization and Detectability.",
        access_level="open_with_citation",
    ),
    DataSourceInfo(
        name="PubMed",
        provider="NCBI / National Library of Medicine",
        source_type="literature",
        access_method="api",
        license="Public domain / NLM terms of use",
        update_method="Scheduled + on-demand harvest via E-utilities",
        url="https://pubmed.ncbi.nlm.nih.gov/",
        layer="evidence",
        role="Literature citations linked to biomarkers, feeding evidence/published-evidence scoring.",
        access_level="public",
    ),
    DataSourceInfo(
        name="Europe PMC",
        provider="EMBL-EBI",
        source_type="literature",
        access_method="api",
        license="Source-dependent; EBI Privacy Notice governs API use",
        update_method="On-demand harvest via REST API",
        url="https://europepmc.org/",
        layer="evidence",
        role="Supplementary literature citations linked to biomarkers.",
        access_level="public",
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
        layer="population",
        role="US population-level cancer statistics, referenced but not queried live.",
        access_level="public",
    ),
)


def sources_for_layer(layer: str) -> tuple[DataSourceInfo, ...]:
    """All registered sources for a given pipeline layer
    (population|molecular|evidence|sensor). No sensor-layer source is
    registered yet — Phase 1 sensor data comes entirely from the internal
    Postgres domain graph (recognition_sensor_uses / sensor_performances),
    not an external source, so an empty tuple there is accurate, not a gap.
    """
    return tuple(s for s in DATA_SOURCES if s.layer == layer)
