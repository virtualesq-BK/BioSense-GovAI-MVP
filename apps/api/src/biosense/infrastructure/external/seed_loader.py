import json
from decimal import Decimal
from pathlib import Path

import structlog

from biosense.config import settings
from biosense.domain.entities.public_health import RawCancerStatRecord

logger = structlog.get_logger()

KR_REGIONS: list[dict[str, str]] = [
    {"code": "KR-11", "name_ko": "서울특별시", "name_en": "Seoul"},
    {"code": "KR-26", "name_ko": "부산광역시", "name_en": "Busan"},
    {"code": "KR-27", "name_ko": "대구광역시", "name_en": "Daegu"},
    {"code": "KR-28", "name_ko": "인천광역시", "name_en": "Incheon"},
    {"code": "KR-29", "name_ko": "광주광역시", "name_en": "Gwangju"},
    {"code": "KR-30", "name_ko": "대전광역시", "name_en": "Daejeon"},
    {"code": "KR-31", "name_ko": "울산광역시", "name_en": "Ulsan"},
    {"code": "KR-41", "name_ko": "경기도", "name_en": "Gyeonggi"},
    {"code": "KR-42", "name_ko": "강원특별자치도", "name_en": "Gangwon"},
    {"code": "KR-43", "name_ko": "충청북도", "name_en": "Chungbuk"},
    {"code": "KR-44", "name_ko": "충청남도", "name_en": "Chungnam"},
    {"code": "KR-45", "name_ko": "전북특별자치도", "name_en": "Jeonbuk"},
    {"code": "KR-46", "name_ko": "전라남도", "name_en": "Jeonnam"},
    {"code": "KR-47", "name_ko": "경상북도", "name_en": "Gyeongbuk"},
    {"code": "KR-48", "name_ko": "경상남도", "name_en": "Gyeongnam"},
    {"code": "KR-49", "name_ko": "제주특별자치도", "name_en": "Jeju"},
    {"code": "KR-50", "name_ko": "세종특별자치시", "name_en": "Sejong"},
]


def _seed_path() -> Path:
    base = Path(__file__).resolve().parents[4]
    return base / settings.public_data_seed_path


def _parse_records(raw: list[dict[str, object]], source_filter: str | None = None) -> list[RawCancerStatRecord]:
    records: list[RawCancerStatRecord] = []
    for item in raw:
        source = str(item["source"]).upper().replace(" (SEED)", "")
        if source_filter and not source.startswith(source_filter):
            continue
        records.append(
            RawCancerStatRecord(
                region_code=str(item["region_code"]),
                region_name_ko=str(item["region_name_ko"]),
                cancer_type=str(item["cancer_type"]),
                incidence_rate=Decimal(str(item["incidence_rate"])) if item.get("incidence_rate") else None,
                mortality_rate=Decimal(str(item["mortality_rate"])) if item.get("mortality_rate") else None,
                data_year=int(item["data_year"]),
                source=source,
            )
        )
    return records


def load_seed_records(source_filter: str | None = None) -> list[RawCancerStatRecord]:
    path = _seed_path()
    logger.info("loading_seed_data", path=str(path), source_filter=source_filter)
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return _parse_records(data, source_filter=source_filter)
