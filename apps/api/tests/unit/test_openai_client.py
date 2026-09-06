from unittest.mock import AsyncMock

import pytest

from biosense.infrastructure.ai.openai_client import create_json_chat_completion


class _FakeError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@pytest.mark.asyncio
async def test_uses_response_format_when_supported() -> None:
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value="ok")

    result = await create_json_chat_completion(
        client, model="gpt-5-mini", messages=[{"role": "user", "content": "hi"}]
    )

    assert result == "ok"
    client.chat.completions.create.assert_awaited_once()
    kwargs = client.chat.completions.create.await_args.kwargs
    assert kwargs["response_format"] == {"type": "json_object"}
    assert kwargs["temperature"] == 0.2


@pytest.mark.asyncio
async def test_retries_without_response_format_on_unsupported_feature() -> None:
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        side_effect=[_FakeError("unsupported_feature"), "ok"]
    )

    result = await create_json_chat_completion(
        client, model="gpt-5-mini", messages=[{"role": "user", "content": "hi"}]
    )

    assert result == "ok"
    assert client.chat.completions.create.await_count == 2
    second_call_kwargs = client.chat.completions.create.await_args_list[1].kwargs
    assert "response_format" not in second_call_kwargs
    assert second_call_kwargs["temperature"] == 0.2


@pytest.mark.asyncio
async def test_retries_without_temperature_when_reasoning_model_rejects_it() -> None:
    """Reproduces the real gpt-5-mini/Codyssey-gateway failure mode: response_format
    is unsupported, and the model also rejects a non-default temperature."""
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        side_effect=[
            _FakeError("unsupported_feature"),
            _FakeError("provider_error"),
            "ok",
        ]
    )

    result = await create_json_chat_completion(
        client, model="gpt-5-mini", messages=[{"role": "user", "content": "hi"}]
    )

    assert result == "ok"
    assert client.chat.completions.create.await_count == 3
    third_call_kwargs = client.chat.completions.create.await_args_list[2].kwargs
    assert "response_format" not in third_call_kwargs
    assert "temperature" not in third_call_kwargs


@pytest.mark.asyncio
async def test_non_unsupported_feature_error_also_retries_without_temperature() -> None:
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        side_effect=[_FakeError("provider_error"), "ok"]
    )

    result = await create_json_chat_completion(
        client, model="gpt-5-mini", messages=[{"role": "user", "content": "hi"}]
    )

    assert result == "ok"
    assert client.chat.completions.create.await_count == 2
    second_call_kwargs = client.chat.completions.create.await_args_list[1].kwargs
    assert "temperature" not in second_call_kwargs


@pytest.mark.asyncio
async def test_reraises_when_all_attempts_fail() -> None:
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        side_effect=[_FakeError("provider_error"), _FakeError("still_broken")]
    )

    with pytest.raises(_FakeError, match="still_broken"):
        await create_json_chat_completion(
            client, model="gpt-5-mini", messages=[{"role": "user", "content": "hi"}]
        )

    assert client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_no_temperature_requested_skips_third_retry() -> None:
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(side_effect=_FakeError("provider_error"))

    with pytest.raises(_FakeError, match="provider_error"):
        await create_json_chat_completion(
            client,
            model="gpt-5-mini",
            messages=[{"role": "user", "content": "hi"}],
            temperature=None,
        )

    client.chat.completions.create.assert_awaited_once()
