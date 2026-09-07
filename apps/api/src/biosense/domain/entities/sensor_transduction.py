"""Domain model for the Sensor Transduction Engine (Phase 1: electrochemical only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SensorPlatformType(str, Enum):
    ELECTROCHEMICAL = "electrochemical"
    OPTICAL = "optical"
    SERS = "sers"
    SPR = "spr"
    FLUORESCENCE = "fluorescence"
    OTHER = "other"

    @property
    def is_phase1_supported(self) -> bool:
        return self is SensorPlatformType.ELECTROCHEMICAL


@dataclass(frozen=True)
class SensorTransductionCandidate:
    platform: SensorPlatformType
    status: str  # "scored" | "not_yet_implemented" | "insufficient_evidence"
    sensor_name: str | None
    feasibility_score: float | None  # 0-100
    rationale: str
    sensitivity: float | None = None
    specificity: float | None = None
    lod_value: float | None = None
    lod_unit: str | None = None
    is_estimated: bool | None = None
    limitations: list[str] = field(default_factory=list)
    supporting_evidence: list[str] = field(default_factory=list)
