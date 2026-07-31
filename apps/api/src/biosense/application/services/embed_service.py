import structlog

from biosense.domain.entities.public_health import PublicDataDocumentRecord
from biosense.infrastructure.ai.embedding_service import EmbeddingService

logger = structlog.get_logger()


class EmbedService:
    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self._embedder = embedding_service or EmbeddingService()

    async def embed_documents(
        self, documents: list[PublicDataDocumentRecord]
    ) -> list[list[float]]:
        if not documents:
            return []
        texts = [doc.content for doc in documents]
        vectors = await self._embedder.embed_texts(texts)
        logger.info("embed_complete", document_count=len(documents), dimensions=len(vectors[0]))
        return vectors
