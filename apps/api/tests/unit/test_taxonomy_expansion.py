"""Contract checks: taxonomy seed must expose strategy-card graph paths 1–4.

Path 5 (tissue-of-origin multimodal report) is intentionally out of scope —
requires RecommendationEngineService multimodal output mode (separate issue).
"""

from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[4]
    / "infra"
    / "db"
    / "migrations"
    / "postgres"
    / "008_taxonomy_expansion.sql"
)

# (ctdna_code_or_None, recognition_code_or_None, sensor_type) must appear in seed SQL
STRATEGY_CARD_PATHS = [
    ("mutation", "dna_hybridization", "AI_NGS"),  # ctDNA + AI NGS
    ("exosomal_mirna", "ai_classification", "AI_NGS"),  # miRNA + AI classification
    (None, None, "SERS"),  # optical/SERS sensing
    ("multi_omics", "ai_classification", None),  # multi-omics panel
]


def test_taxonomy_migration_file_exists() -> None:
    assert MIGRATION.is_file()


def test_strategy_cards_1_to_4_seeded_in_migration() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "exosomal_mirna" in sql
    assert "ctc" in sql
    assert "multi_omics" in sql
    assert "'SERS'" in sql or "SERS" in sql
    assert "AI_NGS" in sql
    assert "CRISPR_dedicated" in sql
    assert "ai_classification" in sql
    assert "miR-21" in sql and "miR-141" in sql and "miR-1246" in sql
    assert "is_estimated" in sql
    assert "multimodal-origin-report" in sql or "원발부위" in sql

    for ctdna, recognition, sensor_type in STRATEGY_CARD_PATHS:
        if ctdna:
            assert ctdna in sql
        if recognition:
            assert recognition in sql
        if sensor_type:
            assert sensor_type in sql


def test_path5_multimodal_origin_deferred() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "OUT OF SCOPE" in sql
    assert "RecommendationEngineService" in sql
