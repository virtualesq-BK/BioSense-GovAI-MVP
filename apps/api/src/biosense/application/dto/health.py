from enum import StrEnum

from pydantic import BaseModel, Field


class DependencyStatus(StrEnum):
    OK = "ok"
    DOWN = "down"


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


class DependenciesHealth(BaseModel):
    postgres: DependencyStatus = DependencyStatus.DOWN
    neo4j: DependencyStatus = DependencyStatus.DOWN


class HealthResponse(BaseModel):
    status: HealthStatus
    version: str = Field(default="0.1.0")
    dependencies: DependenciesHealth
