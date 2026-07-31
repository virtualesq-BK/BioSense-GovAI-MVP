import structlog

from biosense.domain.entities.public_health import (
    PublicDataDocumentRecord,
    TransformedPublicHealthRecord,
)
from biosense.infrastructure.persistence.postgres.ingestion_repository import IngestionRepository

logger = structlog.get_logger()


class StoreService:
    def __init__(self, repo: IngestionRepository) -> None:
        self._repo = repo

    async def store_health_features(self, records: list[TransformedPublicHealthRecord]) -> int:
        count = await self._repo.upsert_public_health_features(records)
        logger.info("store_health_features", count=count)
        return count

    async def store_documents(
        self,
        documents: list[PublicDataDocumentRecord],
        embeddings: list[list[float]],
    ) -> int:
        count = await self._repo.upsert_public_data_documents(documents, embeddings)
        logger.info("store_documents", count=count)
        return count

    async def purge_expired_cache(self) -> int:
        count = await self._repo.purge_expired_cache()
        logger.info("purge_cache", removed=count)
        return count
