from openai import AsyncOpenAI

from biosense.config import settings


def create_openai_client() -> AsyncOpenAI | None:
    if not settings.openai_api_key:
        return None
    kwargs: dict[str, str] = {"api_key": settings.openai_api_key}
    if settings.openai_api_url:
        kwargs["base_url"] = settings.openai_api_url.rstrip("/")
    return AsyncOpenAI(**kwargs)
