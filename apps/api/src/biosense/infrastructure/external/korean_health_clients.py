from decimal import Decimal
from typing import Any
from urllib.parse import parse_qs, urlparse, urlunparse

import httpx
import structlog

from biosense.config import settings
from biosense.domain.entities.public_health import RawCancerStatRecord
from biosense.infrastructure.common.retry import with_retry
from biosense.infrastructure.external.base import PublicDataConnector
from biosense.infrastructure.external.seed_loader import load_seed_records

logger = structlog.get_logger()


class KosisClient(PublicDataConnector):
    """KOSIS Open API — National Cancer Registration Statistics."""

    SOURCE = "KOSIS"

    async def search(
        self, query: str, filters: dict[str, Any] | None = None
    ) -> list[RawCancerStatRecord]:
        """`query` is unused — KOSIS's national cancer table is not keyword-searchable.
        `filters["year"]` selects the statistics year (default 2023)."""
        year = (filters or {}).get("year", 2023)
        return await self.fetch_cancer_statistics(year=year)

    async def fetch(self, identifier: str) -> list[RawCancerStatRecord] | None:
        """Fetch all cancer statistics for a given year (identifier = year string)."""
        try:
            return await self.fetch_cancer_statistics(year=int(identifier))
        except ValueError:
            logger.warning("kosis_fetch_invalid_identifier", identifier=identifier)
            return None

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(settings.kosis_base_url)
            return response.status_code < 500
        except Exception as exc:
            logger.warning("kosis_health_check_failed", error=str(exc))
            return False

    async def fetch_cancer_statistics(self, year: int = 2023) -> list[RawCancerStatRecord]:
        if not settings.kosis_api_key:
            logger.info("kosis_api_key_missing_using_seed")
            return load_seed_records(source_filter="KOSIS")

        async def _call() -> list[RawCancerStatRecord]:
            params = {
                "method": "getList",
                "apiKey": settings.kosis_api_key,
                "itmId": "T001+",
                "objL1": "ALL",
                "format": "json",
                "jsonVD": "Y",
                "prdSe": "Y",
                "newEstPrdCnt": "1",
                "orgId": "117",
                "tblId": "DT_117N_A001",
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(settings.kosis_base_url, params=params)
                response.raise_for_status()
                payload = response.json()

            if not isinstance(payload, list) or not payload:
                raise ValueError("KOSIS returned empty payload")

            records: list[RawCancerStatRecord] = []
            for row in payload:
                if not isinstance(row, dict):
                    continue
                region = str(row.get("C1_NM", row.get("C1", "Unknown")))
                cancer = str(row.get("C2_NM", row.get("ITM_NM", "other"))).lower()
                value = row.get("DT")
                if value is None:
                    continue
                records.append(
                    RawCancerStatRecord(
                        region_code=_map_region_name_to_code(region),
                        region_name_ko=region,
                        cancer_type=_normalize_cancer_type(cancer),
                        incidence_rate=_to_decimal(value),
                        mortality_rate=None,
                        data_year=year,
                        source=self.SOURCE,
                    )
                )
            if not records:
                raise ValueError("KOSIS parse produced zero records")
            return records

        try:
            return await with_retry(_call, operation_name="kosis_fetch")
        except Exception as exc:
            logger.error("kosis_fetch_failed_using_seed", error=str(exc))
            return load_seed_records(source_filter="KOSIS")


class KdcaClient(PublicDataConnector):
    """KDCA — Cancer incidence and mortality statistics."""

    SOURCE = "KDCA"

    async def search(
        self, query: str, filters: dict[str, Any] | None = None
    ) -> list[RawCancerStatRecord]:
        """`query` is unused — KDCA's cancer table is not keyword-searchable.
        `filters["year"]` selects the statistics year (default 2023)."""
        year = (filters or {}).get("year", 2023)
        return await self.fetch_cancer_statistics(year=year)

    async def fetch(self, identifier: str) -> list[RawCancerStatRecord] | None:
        """Fetch all cancer statistics for a given year (identifier = year string)."""
        try:
            return await self.fetch_cancer_statistics(year=int(identifier))
        except ValueError:
            logger.warning("kdca_fetch_invalid_identifier", identifier=identifier)
            return None

    async def health_check(self) -> bool:
        if not settings.has_kdca_api:
            return False
        url = settings.kdca_base_url
        if settings.kdca_api_url:
            url, _ = _split_kdca_url(settings.kdca_api_url)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
            return response.status_code < 500
        except Exception as exc:
            logger.warning("kdca_health_check_failed", error=str(exc))
            return False

    async def fetch_cancer_statistics(self, year: int = 2023) -> list[RawCancerStatRecord]:
        if not settings.has_kdca_api:
            logger.info("kdca_api_missing_using_seed")
            return load_seed_records(source_filter="KDCA")

        if settings.kdca_api_url:
            return await self._fetch_from_configured_url(year)

        return await self._fetch_from_data_go_kr(year)

    async def _fetch_from_configured_url(self, year: int) -> list[RawCancerStatRecord]:
        async def _call() -> list[RawCancerStatRecord]:
            request_url, extra_params = _split_kdca_url(settings.kdca_api_url)
            params = {
                **extra_params,
                "pageNo": extra_params.get("pageNo", "1"),
                "numOfRows": extra_params.get("numOfRows", "100"),
                "searchKeyword": extra_params.get("searchKeyword", "암"),
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(request_url, params=params)
                response.raise_for_status()
                payload = response.json()

            records = _parse_kdca_payload(payload, year=year, source=self.SOURCE)
            if not records:
                raise ValueError("KDCA parse produced zero records")
            return records

        try:
            return await with_retry(_call, operation_name="kdca_fetch_url")
        except Exception as exc:
            logger.error("kdca_fetch_failed_using_seed", error=str(exc))
            return load_seed_records(source_filter="KDCA")

    async def _fetch_from_data_go_kr(self, year: int) -> list[RawCancerStatRecord]:
        async def _call() -> list[RawCancerStatRecord]:
            params = {
                "serviceKey": settings.kdca_api_key,
                "pageNo": 1,
                "numOfRows": 100,
                "resultType": "json",
                "year": year,
            }
            url = f"{settings.kdca_base_url}/getCancerStatistics"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()

            records = _parse_kdca_payload(payload, year=year, source=self.SOURCE)
            if not records:
                raise ValueError("KDCA parse produced zero records")
            return records

        try:
            return await with_retry(_call, operation_name="kdca_fetch")
        except Exception as exc:
            logger.error("kdca_fetch_failed_using_seed", error=str(exc))
            return load_seed_records(source_filter="KDCA")


def _split_kdca_url(raw_url: str) -> tuple[str, dict[str, str]]:
    parsed = urlparse(raw_url.strip())
    query = {k: v[-1] for k, v in parse_qs(parsed.query).items()}
    base = urlunparse(parsed._replace(query=""))
    return base, query


def _parse_kdca_payload(
    payload: object, *, year: int, source: str
) -> list[RawCancerStatRecord]:
    items = _extract_items(payload)
    records: list[RawCancerStatRecord] = []
    for row in items:
        if not isinstance(row, dict):
            continue
        region = str(
            row.get("sidoNm")
            or row.get("region")
            or row.get("areaNm")
            or row.get("ctpvNm")
            or "Unknown"
        )
        cancer = str(
            row.get("cancerNm")
            or row.get("cancer")
            or row.get("dissNm")
            or row.get("healthInfoNm")
            or row.get("cntntsNm")
            or "other"
        ).lower()
        incidence = _to_decimal(
            row.get("incidenceRate")
            or row.get("incdncRate")
            or row.get("dissIncdncRate")
            or row.get("cntntsValue")
        )
        mortality = _to_decimal(row.get("mortalityRate") or row.get("dthRate"))
        if incidence is None and mortality is None and "암" not in cancer:
            continue
        records.append(
            RawCancerStatRecord(
                region_code=_map_region_name_to_code(region),
                region_name_ko=region,
                cancer_type=_normalize_cancer_type(cancer),
                incidence_rate=incidence,
                mortality_rate=mortality,
                data_year=int(row.get("year") or row.get("dataYear") or year),
                source=source,
            )
        )
    return records


def _extract_items(payload: object) -> list[dict[str, object]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]

    if not isinstance(payload, dict):
        return []

    for key in ("data", "result", "items", "list"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested = _extract_items(value)
            if nested:
                return nested

    body = payload.get("response", {}).get("body", payload.get("body", {}))
    if isinstance(body, dict):
        items = body.get("items", body.get("item", body.get("data", [])))
        if isinstance(items, dict):
            item = items.get("item", items)
            if isinstance(item, list):
                return [row for row in item if isinstance(row, dict)]
            if isinstance(item, dict):
                return [item]
        if isinstance(items, list):
            return [row for row in items if isinstance(row, dict)]

    return []


def _to_decimal(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _normalize_cancer_type(name: str) -> str:
    mapping = {
        "폐": "lung",
        "lung": "lung",
        "대장": "colorectal",
        "colorectal": "colorectal",
        "유방": "breast",
        "breast": "breast",
        "간": "liver",
        "liver": "liver",
        "위": "stomach",
        "stomach": "stomach",
        "췌장": "pancreatic",
        "pancreatic": "pancreatic",
    }
    lowered = name.lower()
    for key, code in mapping.items():
        if key in lowered:
            return code
    return "other"


def _map_region_name_to_code(name: str) -> str:
    region_map = {
        "서울": "KR-11",
        "부산": "KR-26",
        "대구": "KR-27",
        "인천": "KR-28",
        "광주": "KR-29",
        "대전": "KR-30",
        "울산": "KR-31",
        "경기": "KR-41",
        "강원": "KR-42",
        "충북": "KR-43",
        "충남": "KR-44",
        "전북": "KR-45",
        "전남": "KR-46",
        "경북": "KR-47",
        "경남": "KR-48",
        "제주": "KR-49",
        "세종": "KR-50",
    }
    for key, code in region_map.items():
        if key in name:
            return code
    return "KR-00"
