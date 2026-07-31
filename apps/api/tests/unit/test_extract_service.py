from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from biosense.application.services.extract_service import ExtractService
from biosense.domain.entities.public_health import RawCancerStatRecord


@pytest.mark.asyncio
async def test_extract_kosis_uses_cache_on_hit() -> None:
    repo = MagicMock()
    repo.load_cached_raw_records = AsyncMock(
        return_value=[
            {
                "region_code": "KR-11",
                "region_name_ko": "서울",
                "cancer_type": "lung",
                "incidence_rate": "42.5",
                "mortality_rate": None,
                "data_year": 2023,
                "source": "KOSIS",
            }
        ]
    )
    kosis = MagicMock()
    kosis.fetch_cancer_statistics = AsyncMock()

    service = ExtractService(repo, kosis=kosis, kdca=MagicMock())
    records = await service.extract_kosis()

    assert len(records) == 1
    assert records[0].cancer_type == "lung"
    kosis.fetch_cancer_statistics.assert_not_called()


@pytest.mark.asyncio
async def test_extract_kosis_fetches_and_caches_on_miss() -> None:
    repo = MagicMock()
    repo.load_cached_raw_records = AsyncMock(return_value=None)
    repo.cache_raw_records = AsyncMock()

    kosis = MagicMock()
    kosis.fetch_cancer_statistics = AsyncMock(
        return_value=[
            RawCancerStatRecord(
                region_code="KR-11",
                region_name_ko="서울",
                cancer_type="lung",
                incidence_rate=Decimal("42.5"),
                mortality_rate=None,
                data_year=2023,
                source="KOSIS",
            )
        ]
    )

    service = ExtractService(repo, kosis=kosis, kdca=MagicMock())
    records = await service.extract_kosis()

    assert len(records) == 1
    kosis.fetch_cancer_statistics.assert_awaited_once()
    repo.cache_raw_records.assert_awaited_once()
