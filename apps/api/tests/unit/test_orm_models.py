import pytest

from biosense.infrastructure.persistence.postgres.base import Base
from biosense.infrastructure.persistence.postgres import models  # noqa: F401


EXPECTED_TABLES = {
    "users",
    "ctdna",
    "cancers",
    "biomarkers",
    "cancer_biomarkers",
    "recognition_strategies",
    "biomarker_recognition_matches",
    "sensors",
    "recognition_sensor_uses",
    "sensor_performances",
    "papers",
    "paper_chunks",
    "paper_biomarkers",
    "paper_sensors",
    "protocols",
    "public_health_features",
    "biomarker_cases",
    "recommendations",
    "graph_sync_log",
    "ingestion_jobs",
    "ingestion_cache",
    "public_data_documents",
    "public_data_chunks",
    "literature_ingestion_jobs",
    "rag_query_logs",
    "rag_evaluations",
}


def test_all_domain_tables_registered() -> None:
    table_names = set(Base.metadata.tables.keys())
    missing = EXPECTED_TABLES - table_names
    assert not missing, f"Missing ORM tables: {missing}"


def test_biomarker_relationships() -> None:
    biomarker_table = Base.metadata.tables["biomarkers"]
    assert "ctdna_id" in biomarker_table.c
    assert "cancer_biomarkers" in Base.metadata.tables


def test_sensor_performance_linked() -> None:
    perf = Base.metadata.tables["sensor_performances"]
    assert "sensor_id" in perf.c
    assert "sensitivity" in perf.c
