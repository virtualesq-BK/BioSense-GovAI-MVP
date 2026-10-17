import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.infrastructure.persistence.postgres.models import SavedReport

MAX_REPORTS_PER_USER = 50


class SavedReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(self, auth_user_id: str) -> list[SavedReport]:
        result = await self._session.execute(
            select(SavedReport)
            .where(SavedReport.auth_user_id == auth_user_id)
            .order_by(SavedReport.created_at.desc())
            .limit(MAX_REPORTS_PER_USER)
        )
        return list(result.scalars().all())

    async def create(
        self, auth_user_id: str, input_data: dict, recommendations: list[dict]
    ) -> SavedReport:
        report = SavedReport(
            id=uuid.uuid4(),
            auth_user_id=auth_user_id,
            input=input_data,
            recommendations=recommendations,
        )
        self._session.add(report)
        await self._session.flush()
        await self._session.refresh(report)
        await self._prune(auth_user_id)
        return report

    async def delete(self, auth_user_id: str, report_id: uuid.UUID) -> bool:
        result = await self._session.execute(
            delete(SavedReport).where(
                SavedReport.id == report_id, SavedReport.auth_user_id == auth_user_id
            )
        )
        return result.rowcount > 0

    async def _prune(self, auth_user_id: str) -> None:
        keep = (
            select(SavedReport.id)
            .where(SavedReport.auth_user_id == auth_user_id)
            .order_by(SavedReport.created_at.desc())
            .limit(MAX_REPORTS_PER_USER)
        )
        await self._session.execute(
            delete(SavedReport).where(
                SavedReport.auth_user_id == auth_user_id, SavedReport.id.not_in(keep)
            )
        )
