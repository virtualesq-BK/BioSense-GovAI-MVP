import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.api.dependencies import get_current_user, get_db_session
from biosense.application.dto.saved_report import SavedReportCreate, SavedReportResponse
from biosense.infrastructure.auth.supabase_jwt import SupabaseAuthUser
from biosense.infrastructure.persistence.postgres.saved_report_repository import (
    SavedReportRepository,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


def _to_response(row) -> SavedReportResponse:
    return SavedReportResponse(
        id=row.id,
        created_at=row.created_at,
        input=row.input,
        recommendations=row.recommendations,
    )


@router.get("", response_model=list[SavedReportResponse])
async def list_reports(
    user: SupabaseAuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[SavedReportResponse]:
    rows = await SavedReportRepository(session).list_for_user(user.sub)
    return [_to_response(r) for r in rows]


@router.post("", response_model=SavedReportResponse, status_code=201)
async def create_report(
    body: SavedReportCreate,
    user: SupabaseAuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> SavedReportResponse:
    row = await SavedReportRepository(session).create(user.sub, body.input, body.recommendations)
    await session.commit()
    return _to_response(row)


@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: uuid.UUID,
    user: SupabaseAuthUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    deleted = await SavedReportRepository(session).delete(user.sub, report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
    await session.commit()
    return Response(status_code=204)
