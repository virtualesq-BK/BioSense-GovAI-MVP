import hashlib
import structlog

from biosense.config import settings
from biosense.infrastructure.ai.openai_client import create_openai_client

logger = structlog.get_logger()


class EmbeddingService:
    """Vectorize text for RAG using OpenAI or deterministic fallback."""

    def __init__(self) -> None:
        self._client = create_openai_client()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if self._client is None:
            logger.info("openai_key_missing_using_deterministic_embeddings")
            return [_deterministic_embedding(t) for t in texts]

        response = await self._client.embeddings.create(
            model=settings.openai_embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_texts([text])
        return vectors[0]


def _deterministic_embedding(text: str, dimensions: int = 1536) -> list[float]:
    """Hash-based pseudo-embedding for offline dev/tests."""
    digest = hashlib.sha256(text.encode()).digest()
    values: list[float] = []
    while len(values) < dimensions:
        for i in range(0, len(digest), 4):
            chunk = digest[i : i + 4]
            if len(chunk) < 4:
                break
            num = int.from_bytes(chunk, "big") / 2**32
            values.append(num * 2 - 1)
            if len(values) >= dimensions:
                break
        digest = hashlib.sha256(digest).digest()
    norm = sum(v * v for v in values) ** 0.5 or 1.0
    return [v / norm for v in values]
