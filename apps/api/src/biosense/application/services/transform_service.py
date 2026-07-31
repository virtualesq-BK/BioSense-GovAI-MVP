import structlog

from biosense.domain.entities.public_health import (
    PublicDataDocumentRecord,
    RawCancerStatRecord,
    TransformedPublicHealthRecord,
)

logger = structlog.get_logger()


class TransformService:
    """Normalize raw API records into domain models and RAG documents."""

    def transform_records(
        self, raw_records: list[RawCancerStatRecord]
    ) -> tuple[list[TransformedPublicHealthRecord], list[PublicDataDocumentRecord]]:
        health_features: list[TransformedPublicHealthRecord] = []
        documents: list[PublicDataDocumentRecord] = []

        for raw in raw_records:
            health_features.extend(self._to_health_features(raw))
            documents.append(self._to_document(raw))

        logger.info(
            "transform_complete",
            raw_count=len(raw_records),
            feature_count=len(health_features),
            document_count=len(documents),
        )
        return health_features, documents

    def _to_health_features(
        self, raw: RawCancerStatRecord
    ) -> list[TransformedPublicHealthRecord]:
        features: list[TransformedPublicHealthRecord] = []
        if raw.incidence_rate is not None:
            features.append(
                TransformedPublicHealthRecord(
                    region_code=raw.region_code,
                    region_name_ko=raw.region_name_ko,
                    cancer_code=raw.cancer_type,
                    feature_type="incidence",
                    value=raw.incidence_rate,
                    unit="per_100k",
                    data_year=raw.data_year,
                    source=raw.source,
                )
            )
        if raw.mortality_rate is not None:
            features.append(
                TransformedPublicHealthRecord(
                    region_code=raw.region_code,
                    region_name_ko=raw.region_name_ko,
                    cancer_code=raw.cancer_type,
                    feature_type="mortality",
                    value=raw.mortality_rate,
                    unit="per_100k",
                    data_year=raw.data_year,
                    source=raw.source,
                )
            )
        return features

    def _to_document(self, raw: RawCancerStatRecord) -> PublicDataDocumentRecord:
        incidence = f"{raw.incidence_rate}" if raw.incidence_rate is not None else "N/A"
        mortality = f"{raw.mortality_rate}" if raw.mortality_rate is not None else "N/A"
        content = (
            f"Korean public health cancer statistics for {raw.region_name_ko} "
            f"({raw.region_code}). Cancer type: {raw.cancer_type}. "
            f"Incidence rate: {incidence} per 100,000. "
            f"Mortality rate: {mortality} per 100,000. "
            f"Data year: {raw.data_year}. Source: {raw.source}."
        )
        external_key = (
            f"ph:{raw.source}:{raw.region_code}:{raw.cancer_type}:{raw.data_year}"
        )
        return PublicDataDocumentRecord(
            external_key=external_key,
            source=raw.source,
            title=f"{raw.region_name_ko} {raw.cancer_type} cancer statistics ({raw.data_year})",
            content=content,
            data_year=raw.data_year,
            metadata={
                "region_code": raw.region_code,
                "cancer_type": raw.cancer_type,
                "incidence_rate": str(raw.incidence_rate) if raw.incidence_rate else None,
                "mortality_rate": str(raw.mortality_rate) if raw.mortality_rate else None,
            },
        )
