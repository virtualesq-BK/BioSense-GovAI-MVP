from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RawCancerStatRecord:
    region_code: str
    region_name_ko: str
    cancer_type: str
    incidence_rate: Decimal | None
    mortality_rate: Decimal | None
    data_year: int
    source: str


@dataclass(frozen=True)
class TransformedPublicHealthRecord:
    region_code: str
    region_name_ko: str
    cancer_code: str
    feature_type: str
    value: Decimal
    unit: str
    data_year: int
    source: str


@dataclass(frozen=True)
class PublicDataDocumentRecord:
    external_key: str
    source: str
    title: str
    content: str
    data_year: int
    metadata: dict[str, object]
