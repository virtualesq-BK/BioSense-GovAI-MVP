import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SavedReportCreate(BaseModel):
    input: dict[str, Any]
    recommendations: list[dict[str, Any]] = Field(max_length=50)


class SavedReportResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    input: dict[str, Any]
    recommendations: list[dict[str, Any]]
