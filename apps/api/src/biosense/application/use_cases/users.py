from biosense.application.dto.user import UserResponse
from biosense.infrastructure.auth.supabase_jwt import SupabaseAuthUser
from biosense.infrastructure.persistence.postgres.user_repository import UserRepository


async def get_or_create_current_user(
    repo: UserRepository,
    auth_user: SupabaseAuthUser,
) -> UserResponse:
    email = auth_user.email or f"{auth_user.sub}@users.supabase.local"
    user = await repo.upsert_from_auth(auth_user_id=auth_user.sub, email=email)
    return UserResponse(
        id=str(user.id),
        auth_user_id=user.auth_user_id,
        email=user.email,
        org_name=user.org_name,
        role=user.role,
        created_at=user.created_at.isoformat(),
    )
