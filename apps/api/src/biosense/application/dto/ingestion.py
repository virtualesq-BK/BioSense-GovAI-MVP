from collections.abc import AsyncGenerator
from typing import Literal

from pydantic import BaseModel, Field


class TriggerIngestionRequest(BaseModel):
    source: Literal["kosis", "kdca", "full"] = "full"
    year: int = Field(default=2023, ge=2000, le=2100)


class IngestionJobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    source: str
    records_extracted: int
    records_transformed: int
    records_embedded: int
    records_stored: int
    error_message: str | None
    started_at: str | None
    finished_at: str | None
    created_at: str


class TriggerIngestionResponse(BaseModel):
    job_id: str
    message: str


class MonitoringStatusResponse(BaseModel):
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    last_success_at: str | None
    last_job_status: str | None
    recent_jobs: list[IngestionJobResponse]


class RegionResponse(BaseModel):
    code: str
    name_ko: str
    name_en: str


class CancerStatsResponse(BaseModel):
    region_code: str
    cancer_type: str
    incidence_rate: float | None
    mortality_rate: float | None
    data_year: int
    source: str
