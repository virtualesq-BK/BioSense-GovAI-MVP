from typing import Any

from openai import AsyncOpenAI

from biosense.config import settings


def create_openai_client() -> AsyncOpenAI | None:
    if not settings.openai_api_key:
        return None
    kwargs: dict[str, Any] = {
        "api_key": settings.openai_api_key,
        # The openai SDK's default User-Agent ("OpenAI/Python ...") is blocked by
        # this project's OpenAI-compatible proxy's WAF (verified 2026-09-07: the
        # same request succeeds with any other User-Agent). Override it so SDK
        # calls aren't silently 403'd.
        "default_headers": {"User-Agent": "BioSense-GovAI/1.0"},
    }
    if settings.openai_api_url:
        kwargs["base_url"] = settings.openai_api_url.rstrip("/")
    return AsyncOpenAI(**kwargs)
