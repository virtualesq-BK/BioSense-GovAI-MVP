"""Tests for Phase 2: metadata-only methylation integration and CRISPR
citation-linked evidence. See docs/data-feasibility-phase2.md for the audit
that scoped this phase.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from biosense.application.services.molecular_characterization_service import (
    MolecularCharacterizationService,
)
from biosense.application.services.molecular_detectability_service import (
    MolecularDetectabilityService,
)
from biosense.application.services.molecular_recognition_service import MolecularRecognitionEngine
from biosense.domain.entities.biomarker_dimension import BiomarkerEvidenceStatus
from biosense.domain.entities.genomics import RawGdcMethylationFileRecord
from biosense.domain.entities.methylation import CANCER_TYPE_TO_TCGA_PROJECTS
from biosense.domain.entities.molecular_characterization import MolecularCharacterizationResult
from biosense.domain.entities.molecular_recognition import (
    RecognitionRecommendation,
    RecognitionStrategyType,
)
from biosense.domain.entities.recognition_compatibility import (
    CompatibilityEvidenceLevel,
    RecognitionCompatibilityTable,
)
from biosense.infrastructure.external.gdc_client import GdcClient, _parse_methylation_file

SAMPLE_METHYLATION_FILES = {
    "data": {
        "hits": [
            {
                "id": "file-1",
                "file_id": "file-1",
                "file_name": "jhu-usc.edu_LUAD.HumanMethylation450.1.lvl-3.txt",
                "data_type": "Methylation Beta Value",
                "platform": "Illumina Human Methylation 450",
                "access": "open",
                "cases": [
                    {
                        "project": {"project_id": "TCGA-LUAD"},
                        "samples": [{"sample_type": "Primary Tumor"}],
                    }
                ],
            }
        ]
    }
}


def _mock_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    return resp


def test_parse_methylation_file() -> None:
    record = _parse_methylation_file(SAMPLE_METHYLATION_FILES["data"]["hits"][0])
    assert record.file_id == "file-1"
    assert record.data_type == "Methylation Beta Value"
    assert record.platform == "Illumina Human Methylation 450"
    assert record.access == "open"
    assert record.project_id == "TCGA-LUAD"
    assert record.sample_types == ["Primary Tumor"]


@pytest.mark.asyncio
async def test_search_methylation_files_success() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=_mock_response(SAMPLE_METHYLATION_FILES))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "biosense.infrastructure.external.gdc_client.httpx.AsyncClient",
        return_value=mock_client,
    ):
        client = GdcClient()
        records = await client.search_methylation_files(project_id="TCGA-LUAD")

    assert len(records) == 1
    assert records[0].file_id == "file-1"
    called_params = mock_client.get.await_args.kwargs["params"]
    assert "filters" in called_params


@pytest.mark.asyncio
async def test_search_methylation_files_returns_empty_on_failure() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=ConnectionError("offline"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "biosense.infrastructure.external.gdc_client.httpx.AsyncClient",
        return_value=mock_client,
    ):
        client = GdcClient()
        records = await client.search_methylation_files(project_id="TCGA-LUAD")

    assert records == []


class FakeGdcMethylationClient:
    def __init__(self, files_by_project: dict[str, list[RawGdcMethylationFileRecord]]):
        self._files = files_by_project

    async def search_methylation_files(self, *, project_id: str, size: int = 20):
        return self._files.get(project_id, [])


def _methylation_biomarker():
    return SimpleNamespace(
        id="b2",
        name="Gene X methylation",
        gene_symbol="GENEX",
        description=None,
        ctdna=SimpleNamespace(code="methylation"),
        papers=[],
    )


@pytest.mark.asyncio
async def test_methylation_characterization_partially_supported() -> None:
    files = [
        RawGdcMethylationFileRecord(
            file_id="f1",
            file_name="f1.txt",
            data_type="Methylation Beta Value",
            platform="Illumina Human Methylation 450",
            access="open",
            project_id="TCGA-LUAD",
            case_count=1,
            sample_types=["Primary Tumor"],
        )
    ]
    gdc = FakeGdcMethylationClient({"TCGA-LUAD": files, "TCGA-LUSC": []})
    service = MolecularCharacterizationService(gdc=gdc)

    result = await service.characterize(_methylation_biomarker(), cancer_code="lung")

    assert result.dimension == "methylation"
    assert result.evidence_status == BiomarkerEvidenceStatus.PARTIALLY_SUPPORTED
    assert "metadata" in result.evidence_status_reason.lower() or "GDC" in result.evidence_status_reason
    assert result.evidence_status != BiomarkerEvidenceStatus.SUPPORTED
    assert any("GDC methylation array file" in c for c in result.molecular_characteristics)
    # never fabricate a quantitative value anywhere in the output
    assert "beta" not in " ".join(result.molecular_characteristics).lower() or "no quantitative" in " ".join(
        result.limitations
    ).lower()


@pytest.mark.asyncio
async def test_methylation_characterization_insufficient_evidence_when_no_files() -> None:
    gdc = FakeGdcMethylationClient({})
    service = MolecularCharacterizationService(gdc=gdc)

    result = await service.characterize(_methylation_biomarker(), cancer_code="lung")

    assert result.evidence_status == BiomarkerEvidenceStatus.INSUFFICIENT_EVIDENCE
    assert result.evidence_status != BiomarkerEvidenceStatus.SUPPORTED


@pytest.mark.asyncio
async def test_methylation_characterization_unknown_cancer_type() -> None:
    gdc = FakeGdcMethylationClient({})
    service = MolecularCharacterizationService(gdc=gdc)

    result = await service.characterize(_methylation_biomarker(), cancer_code="not_a_real_cancer_type")

    assert result.evidence_status == BiomarkerEvidenceStatus.INSUFFICIENT_EVIDENCE


def test_tcga_project_mapping_covers_mvp_cancer_types() -> None:
    assert CANCER_TYPE_TO_TCGA_PROJECTS["lung"] == ["TCGA-LUAD", "TCGA-LUSC"]
    assert CANCER_TYPE_TO_TCGA_PROJECTS["colorectal"] == ["TCGA-COAD", "TCGA-READ"]
    assert CANCER_TYPE_TO_TCGA_PROJECTS["breast"] == ["TCGA-BRCA"]


def test_methylation_detectability_stays_honest() -> None:
    result = MolecularCharacterizationResult(
        biomarker="Gene X methylation",
        dimension="methylation",
        molecular_characteristics=["GDC methylation array file(s) identified..."],
        detectability=None,
        specificity_features=["Sample types observed in GDC file metadata: Primary Tumor."],
        limitations=[],
        evidence=[],
        evidence_status=BiomarkerEvidenceStatus.PARTIALLY_SUPPORTED,
        evidence_status_reason="test",
    )
    detectability = MolecularDetectabilityService().assess(result)

    # No abundance/allele-fraction data source exists for metadata-only methylation.
    assert detectability.abundance is None
    assert detectability.allele_fraction is None
    assert detectability.structural_signal == "unknown"
    assert detectability.background_interference == "unknown"
    # sample_compatibility is the one field this phase can honestly derive.
    assert detectability.sample_compatibility == "Primary Tumor"


def test_compatibility_matrix_methylation_entries_are_insufficient_evidence() -> None:
    table = RecognitionCompatibilityTable()
    from biosense.domain.entities.biomarker_dimension import BiomarkerDimensionType

    rules = table.for_dimension(BiomarkerDimensionType.METHYLATION)
    assert len(rules) >= 2
    for rule in rules:
        assert rule.evidence_level == CompatibilityEvidenceLevel.INSUFFICIENT_EVIDENCE


# --- CRISPR citation-linked evidence -----------------------------------


def _crispr_recommendation() -> RecognitionRecommendation:
    return RecognitionRecommendation(
        strategy=RecognitionStrategyType.CRISPR_CAS,
        status="scored",
        compatibility_score=70.0,
        rationale="Heuristic estimate from molecular characterization only.",
        confidence=0.3,
    )


class FakePubmedClient:
    def __init__(self, papers):
        self._papers = papers

    async def search_and_fetch(self, query, *, max_results=20):
        return self._papers


@pytest.mark.asyncio
async def test_attach_crispr_citations_found() -> None:
    paper = SimpleNamespace(external_id="pmid:123", title="CRISPR detection of GENEX", doi="10.1/x")
    pubmed = FakePubmedClient([paper])
    engine = MolecularRecognitionEngine()

    out = await engine.attach_crispr_citations(
        [_crispr_recommendation()], gene_symbol="GENEX", pubmed=pubmed
    )

    assert len(out) == 1
    assert out[0].evidence_source == "HEURISTIC_WITH_CITATIONS"
    assert len(out[0].citation_evidence) == 1
    assert out[0].citation_evidence[0].external_id == "pmid:123"
    assert out[0].citation_evidence[0].evidence_type == "literature_citation"


@pytest.mark.asyncio
async def test_attach_crispr_citations_none_found_stays_heuristic() -> None:
    pubmed = FakePubmedClient([])
    engine = MolecularRecognitionEngine()

    out = await engine.attach_crispr_citations(
        [_crispr_recommendation()], gene_symbol="GENEX", pubmed=pubmed
    )

    assert out[0].evidence_source == "HEURISTIC"
    assert out[0].citation_evidence == []
    assert "No relevant CRISPR-Cas literature citations" in out[0].rationale


@pytest.mark.asyncio
async def test_attach_crispr_citations_skips_non_crispr_strategies() -> None:
    dna_rec = RecognitionRecommendation(
        strategy=RecognitionStrategyType.DNA_HYBRIDIZATION,
        status="scored",
        compatibility_score=80.0,
        rationale="r",
    )
    pubmed = FakePubmedClient([SimpleNamespace(external_id="pmid:1", title="t", doi=None)])
    engine = MolecularRecognitionEngine()

    out = await engine.attach_crispr_citations([dna_rec], gene_symbol="GENEX", pubmed=pubmed)

    assert out[0].evidence_source == "HEURISTIC"
    assert out[0].citation_evidence == []


@pytest.mark.asyncio
async def test_attach_crispr_citations_include_citations_false_is_noop() -> None:
    engine = MolecularRecognitionEngine()
    recs = [_crispr_recommendation()]

    out = await engine.attach_crispr_citations(
        recs, gene_symbol="GENEX", include_citations=False
    )

    assert out == recs
