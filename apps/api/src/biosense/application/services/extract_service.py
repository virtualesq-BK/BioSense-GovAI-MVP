from dataclasses import asdict
from decimal import Decimal

import structlog

from biosense.domain.entities.public_health import RawCancerStatRecord
from biosense.infrastructure.external.korean_health_clients import KdcaClient, KosisClient
from biosense.infrastructure.persistence.postgres.ingestion_repository import IngestionRepository

logger = structlog.get_logger()


class ExtractService:
    def __init__(
        self,
        repo: IngestionRepository,
        kosis: KosisClient | None = None,
        kdca: KdcaClient | None = None,
    ) -> None:
        self._repo = repo
        self._kosis = kosis or KosisClient()
        self._kdca = kdca or KdcaClient()

    async def extract_kosis(self, year: int = 2023) -> list[RawCancerStatRecord]:
        cache_key = f"kosis:cancer:{year}"
        cached = await self._repo.load_cached_raw_records(cache_key)
        if cached:
            logger.info("extract_cache_hit", source="KOSIS", cache_key=cache_key)
            return [_dict_to_raw(r) for r in cached]

        records = await self._kosis.fetch_cancer_statistics(year=year)
        await self._repo.cache_raw_records(cache_key, "KOSIS", [asdict(r) for r in records])
        logger.info("extract_complete", source="KOSIS", count=len(records))
        return records

    async def extract_kdca(self, year: int = 2023) -> list[RawCancerStatRecord]:
        cache_key = f"kdca:cancer:{year}"
        cached = await self._repo.load_cached_raw_records(cache_key)
        if cached:
            logger.info("extract_cache_hit", source="KDCA", cache_key=cache_key)
            return [_dict_to_raw(r) for r in cached]

        records = await self._kdca.fetch_cancer_statistics(year=year)
        await self._repo.cache_raw_records(cache_key, "KDCA", [asdict(r) for r in records])
        logger.info("extract_complete", source="KDCA", count=len(records))
        return records


def _dict_to_raw(data: dict) -> RawCancerStatRecord:
    return RawCancerStatRecord(
        region_code=str(data["region_code"]),
        region_name_ko=str(data["region_name_ko"]),
        cancer_type=str(data["cancer_type"]),
        incidence_rate=Decimal(str(data["incidence_rate"])) if data.get("incidence_rate") else None,
        mortality_rate=Decimal(str(data["mortality_rate"])) if data.get("mortality_rate") else None,
        data_year=int(data["data_year"]),
        source=str(data["source"]),
    )
