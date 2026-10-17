from decimal import Decimal

from biosense.application.services.transform_service import TransformService
from biosense.domain.entities.public_health import RawCancerStatRecord


def test_transform_creates_incidence_and_mortality_features() -> None:
    raw = RawCancerStatRecord(
        region_code="KR-11",
        region_name_ko="서울특별시",
        cancer_type="lung",
        incidence_rate=Decimal("42.5"),
        mortality_rate=Decimal("28.3"),
        data_year=2023,
        source="KOSIS",
    )
    service = TransformService()
    features, documents = service.transform_records([raw])

    assert len(features) == 2
    assert {f.feature_type for f in features} == {"incidence", "mortality"}
    assert features[0].region_code == "KR-11"
    assert len(documents) == 1
    assert "서울특별시" in documents[0].content
    assert documents[0].external_key == "ph:KOSIS:KR-11:lung:2023"


def test_transform_incidence_only() -> None:
    raw = RawCancerStatRecord(
        region_code="KR-26",
        region_name_ko="부산광역시",
        cancer_type="stomach",
        incidence_rate=Decimal("45.8"),
        mortality_rate=None,
        data_year=2023,
        source="KOSIS",
    )
    features, _ = TransformService().transform_records([raw])
    assert len(features) == 1
    assert features[0].feature_type == "incidence"
