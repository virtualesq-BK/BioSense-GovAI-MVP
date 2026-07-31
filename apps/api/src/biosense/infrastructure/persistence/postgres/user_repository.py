import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.infrastructure.persistence.postgres.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_auth_user_id(self, auth_user_id: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.auth_user_id == auth_user_id)
        )
        return result.scalar_one_or_none()

    async def upsert_from_auth(
        self,
        *,
        auth_user_id: str,
        email: str,
        org_name: str | None = None,
        role: str = "researcher",
    ) -> User:
        user = await self.get_by_auth_user_id(auth_user_id)
        if user is None:
            user = User(
                id=uuid.uuid4(),
                auth_user_id=auth_user_id,
                email=email,
                org_name=org_name,
                role=role,
            )
            self._session.add(user)
        else:
            user.email = email
            if org_name is not None:
                user.org_name = org_name
        await self._session.commit()
        await self._session.refresh(user)
        return user
