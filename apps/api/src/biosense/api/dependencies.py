from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.infrastructure.auth.supabase_jwt import SupabaseAuthUser, verify_supabase_jwt
from biosense.infrastructure.persistence.postgres.session import async_session_factory

_bearer = HTTPBearer(auto_error=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> SupabaseAuthUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        return verify_supabase_jwt(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> SupabaseAuthUser | None:
    if credentials is None or not credentials.credentials:
        return None
    try:
        return verify_supabase_jwt(credentials.credentials)
    except ValueError:
        return None
