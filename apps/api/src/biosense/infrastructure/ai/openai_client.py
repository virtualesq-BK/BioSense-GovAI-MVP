from typing import Any

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from biosense.config import settings


async def create_json_chat_completion(
    client: AsyncOpenAI,
    *,
    model: str,
    messages: list[ChatCompletionMessageParam],
    temperature: float | None = 0.2,
) -> ChatCompletion:
    """Chat completion that asks for JSON output, tolerating two provider quirks
    verified 2026-09-07 against a Codyssey-hosted OpenAI-compatible gateway:

    1. `response_format={"type": "json_object"}` is rejected with a 400
       `unsupported_feature` even though the model works fine otherwise.
    2. Reasoning-style models (e.g. gpt-5-mini on that gateway) accept only the
       default `temperature` (1.0) and return a 502 `provider_error` for any
       other value — a request that is otherwise byte-for-byte identical
       succeeds once `temperature` is omitted.

    Every call site's system/user prompt already instructs the model to return
    JSON, so both quirks are safe to route around: drop `response_format` on
    `unsupported_feature`, then drop `temperature` too if the call still fails.
    Any other error propagates from the final attempt.
    """
    kwargs: dict[str, Any] = {"model": model, "messages": messages}
    if temperature is not None:
        kwargs["temperature"] = temperature

    try:
        return await client.chat.completions.create(
            **kwargs, response_format={"type": "json_object"}
        )
    except Exception as exc:
        if getattr(exc, "code", None) != "unsupported_feature":
            return await _retry_without_temperature(client, kwargs, exc)
        try:
            return await client.chat.completions.create(**kwargs)
        except Exception as exc2:
            return await _retry_without_temperature(client, kwargs, exc2)


async def _retry_without_temperature(
    client: AsyncOpenAI, kwargs: dict[str, Any], original_exc: Exception
) -> ChatCompletion:
    if "temperature" not in kwargs:
        raise original_exc
    retry_kwargs = {k: v for k, v in kwargs.items() if k != "temperature"}
    return await client.chat.completions.create(**retry_kwargs)


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
