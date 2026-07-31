import pytest

from biosense.infrastructure.ai.embedding_service import EmbeddingService, _deterministic_embedding


@pytest.mark.asyncio
async def test_deterministic_embedding_dimensions() -> None:
    service = EmbeddingService()
    service._client = None
    vectors = await service.embed_texts(["test cancer statistics"])
    assert len(vectors) == 1
    assert len(vectors[0]) == 1536


def test_deterministic_embedding_is_stable() -> None:
    a = _deterministic_embedding("KR-11 lung cancer")
    b = _deterministic_embedding("KR-11 lung cancer")
    assert a == b
