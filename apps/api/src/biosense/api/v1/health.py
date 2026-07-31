from fastapi import APIRouter

from biosense.application.dto.health import HealthResponse
from biosense.application.use_cases.health import get_health

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return await get_health()
