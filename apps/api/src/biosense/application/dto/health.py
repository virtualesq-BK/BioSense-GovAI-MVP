from enum import Enum

from pydantic import BaseModel, Field


class DependencyStatus(str, Enum):
    OK = "ok"
    DOWN = "down"


class HealthStatus(str, Enum):
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
