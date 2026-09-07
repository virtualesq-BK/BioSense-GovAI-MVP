from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from biosense.application.services.molecular_characterization_service import (
    MolecularCharacterizationService,
)
from biosense.domain.entities.molecular_characterization import INSUFFICIENT_EVIDENCE


@dataclass
class FakeGene:
    gene_id: str
    name: str
    biotype: str


class FakeGdcClient:
    def __init__(self, genes=None, mutation_count=None):
        self._genes = genes or []
        self._mutation_count = mutation_count

    async def search_genes(self, symbol, *, size: int = 5):
        return self._genes

    async def count_mutations_for_gene(self, gene_symbol):
        return self._mutation_count


def _biomarker(*, gene_symbol="KRAS", ctdna_code="mutation", papers=None, description=None):
    return SimpleNamespace(
        id="b1",
        name="KRAS G12D mutation",
        gene_symbol=gene_symbol,
        description=description,
        ctdna=SimpleNamespace(code=ctdna_code) if ctdna_code else None,
        papers=papers or [],
    )


@pytest.mark.asyncio
async def test_characterize_with_no_biomarker_marks_missing():
    service = MolecularCharacterizationService(gdc=FakeGdcClient())
    result = await service.characterize(None, cancer_code="lung")

    assert result.dimension == "mutation"
    assert result.detectability.missing_data is True
    assert INSUFFICIENT_EVIDENCE in result.limitations[0]


@pytest.mark.asyncio
async def test_characterize_non_mutation_dimension_not_supported():
    # "methylation" is now handled by a dedicated Phase 2 metadata-only path
    # (see test_phase2_methylation_and_crispr_citations.py) — this test covers
    # a dimension that is still genuinely unimplemented, e.g. "fusion".
    service = MolecularCharacterizationService(gdc=FakeGdcClient())
    biomarker = _biomarker(ctdna_code="fusion")

    result = await service.characterize(biomarker, cancer_code="lung")

    assert result.dimension == "fusion"
    assert result.molecular_characteristics == []
    assert "not yet supported" in result.limitations[0]


@pytest.mark.asyncio
async def test_characterize_with_real_gdc_data_populates_fields():
    gene = FakeGene(gene_id="ENSG1", name="KRAS proto-oncogene", biotype="protein_coding")
    gdc = FakeGdcClient(genes=[gene], mutation_count=141)
    paper = SimpleNamespace(source="PubMed", external_id="pmid:1", title="A paper")
    biomarker = _biomarker(papers=[paper])

    service = MolecularCharacterizationService(gdc=gdc)
    result = await service.characterize(biomarker, cancer_code="lung")

    assert result.biomarker == "KRAS G12D mutation"
    assert result.dimension == "mutation"
    assert any("KRAS" in c for c in result.molecular_characteristics)
    assert result.detectability.is_detectable_in_ctdna is True
    assert result.detectability.mutation_count == 141
    assert result.detectability.missing_data is False
    assert len(result.evidence) == 2  # gene record + paper
    assert any("Research use only" in lim for lim in result.limitations)


@pytest.mark.asyncio
async def test_characterize_with_no_gdc_data_reports_insufficient_evidence():
    gdc = FakeGdcClient(genes=[], mutation_count=None)
    biomarker = _biomarker(papers=[])

    service = MolecularCharacterizationService(gdc=gdc)
    result = await service.characterize(biomarker, cancer_code="lung")

    assert result.molecular_characteristics == []
    assert result.detectability.missing_data is True
    assert any(INSUFFICIENT_EVIDENCE in lim for lim in result.limitations)


@pytest.mark.asyncio
async def test_characterize_without_gene_symbol_reports_insufficient_evidence():
    biomarker = _biomarker(gene_symbol=None)
    service = MolecularCharacterizationService(gdc=FakeGdcClient())

    result = await service.characterize(biomarker, cancer_code="lung")

    assert any("no gene_symbol" in lim for lim in result.limitations)
