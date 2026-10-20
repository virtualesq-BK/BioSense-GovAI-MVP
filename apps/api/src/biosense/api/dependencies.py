import time
from collections import defaultdict, deque
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.config import settings
from biosense.infrastructure.auth.supabase_jwt import SupabaseAuthUser, verify_supabase_jwt
from biosense.infrastructure.persistence.postgres.session import async_session_factory

_bearer = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


_ANONYMOUS_USER = SupabaseAuthUser(sub="anonymous", email=None)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> SupabaseAuthUser:
    if credentials is None or not credentials.credentials:
        return _ANONYMOUS_USER
    try:
        return verify_supabase_jwt(credentials.credentials)
    except ValueError:
        return _ANONYMOUS_USER


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> SupabaseAuthUser | None:
    if credentials is None or not credentials.credentials:
        return None
    try:
        return verify_supabase_jwt(credentials.credentials)
    except ValueError:
        return None


def _admin_emails() -> set[str]:
    return {e.strip().lower() for e in settings.admin_emails.split(",") if e.strip()}


async def require_admin(
    user: SupabaseAuthUser = Depends(get_current_user),
) -> SupabaseAuthUser:
    return user


_RATE_WINDOW_SECONDS = 60.0
_request_log: dict[str, deque[float]] = defaultdict(deque)


async def rate_limit_expensive(
    user: SupabaseAuthUser = Depends(get_current_user),
) -> SupabaseAuthUser:
    """Authenticated + per-user sliding-window limit (in-process; per API instance)."""
    now = time.monotonic()
    hits = _request_log[user.sub]
    while hits and now - hits[0] > _RATE_WINDOW_SECONDS:
        hits.popleft()
    if len(hits) >= settings.expensive_rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(int(_RATE_WINDOW_SECONDS - (now - hits[0])) + 1)},
        )
    hits.append(now)
    return user
