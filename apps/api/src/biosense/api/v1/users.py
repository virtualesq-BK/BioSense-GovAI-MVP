from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.api.dependencies import get_current_user, get_db_session
from biosense.application.dto.user import UserResponse
from biosense.application.use_cases.users import get_or_create_current_user
from biosense.infrastructure.auth.supabase_jwt import SupabaseAuthUser
from biosense.infrastructure.persistence.postgres.user_repository import UserRepository

router = APIRouter(tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    auth_user: SupabaseAuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    repo = UserRepository(session)
    return await get_or_create_current_user(repo, auth_user)
