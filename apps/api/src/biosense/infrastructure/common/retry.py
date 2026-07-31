from collections.abc import Awaitable, Callable
from typing import TypeVar

import structlog
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from biosense.config import settings

logger = structlog.get_logger()
T = TypeVar("T")


async def with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    operation_name: str,
    max_attempts: int | None = None,
) -> T:
    attempts = max_attempts or settings.ingestion_retry_max_attempts
    delay = settings.ingestion_retry_base_delay_seconds

    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=delay, min=delay, max=delay * 8),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        reraise=True,
    ):
        with attempt:
            try:
                return await operation()
            except Exception as exc:
                logger.warning(
                    "retry_attempt_failed",
                    operation=operation_name,
                    attempt=attempt.retry_state.attempt_number,
                    error=str(exc),
                )
                raise

    raise RuntimeError(f"Retry exhausted for {operation_name}")
