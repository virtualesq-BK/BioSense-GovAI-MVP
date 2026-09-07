"""Sensor Transduction Engine (Phase 1: electrochemical platform only).

Input: a scored `RecognitionRecommendation` plus the Postgres
`recognition_sensor_uses` / `sensor_performances` graph for that recognition
strategy. Output: one `SensorTransductionCandidate` per platform in the full
enum — only ELECTROCHEMICAL is scored from real rows for Phase 1; the rest are
returned as "documented platform, not yet implemented".
"""

from __future__ import annotations

from biosense.domain.entities.molecular_recognition import RecognitionRecommendation
from biosense.domain.entities.sensor_transduction import (
    SensorPlatformType,
    SensorTransductionCandidate,
)
from biosense.infrastructure.persistence.postgres.models import RecognitionSensorUse

_NOT_YET_IMPLEMENTED_RATIONALE = (
    "Documented sensor transduction platform, not yet implemented in this "
    "platform (Phase 1 covers electrochemical transduction only)."
)


class SensorTransductionEngine:
    def transduce(
        self,
        recognition: RecognitionRecommendation,
        *,
        sensor_uses: list[RecognitionSensorUse],
    ) -> list[SensorTransductionCandidate]:
        results: list[SensorTransductionCandidate] = []
        electrochemical_uses = [
            u for u in sensor_uses if u.sensor is not None and u.sensor.sensor_type == "electrochemical"
        ]

        for platform in SensorPlatformType:
            if not platform.is_phase1_supported:
                results.append(
                    SensorTransductionCandidate(
                        platform=platform,
                        status="not_yet_implemented",
                        sensor_name=None,
                        feasibility_score=None,
                        rationale=_NOT_YET_IMPLEMENTED_RATIONALE,
                        limitations=[_NOT_YET_IMPLEMENTED_RATIONALE],
                    )
                )
                continue
            results.append(self._score_electrochemical(recognition, electrochemical_uses))
        return results

    def _score_electrochemical(
        self,
        recognition: RecognitionRecommendation,
        uses: list[RecognitionSensorUse],
    ) -> SensorTransductionCandidate:
        if recognition.status != "scored" or recognition.compatibility_score is None:
            return SensorTransductionCandidate(
                platform=SensorPlatformType.ELECTROCHEMICAL,
                status="insufficient_evidence",
                sensor_name=None,
                feasibility_score=None,
                rationale=(
                    "Insufficient evidence — no scored recognition strategy to transduce "
                    "into an electrochemical sensor candidate."
                ),
                limitations=["Insufficient evidence"],
            )

        if not uses:
            return SensorTransductionCandidate(
                platform=SensorPlatformType.ELECTROCHEMICAL,
                status="insufficient_evidence",
                sensor_name=None,
                feasibility_score=None,
                rationale=(
                    "Insufficient evidence — no electrochemical sensor is linked to this "
                    "recognition strategy in the domain graph."
                ),
                limitations=["Insufficient evidence"],
            )

        best = max(uses, key=lambda u: float(u.efficiency or 0))
        efficiency = float(best.efficiency) if best.efficiency is not None else None
        performances = sorted(
            (p for p in (best.sensor.performances or [])),
            key=lambda p: (p.sensitivity or 0),
            reverse=True,
        )
        perf = performances[0] if performances else None

        feasibility = None
        if efficiency is not None:
            feasibility = round(
                (efficiency * 0.6 + (recognition.compatibility_score / 100.0) * 0.4) * 100.0, 2
            )

        return SensorTransductionCandidate(
            platform=SensorPlatformType.ELECTROCHEMICAL,
            status="scored",
            sensor_name=best.sensor.name,
            feasibility_score=feasibility,
            rationale=(
                f"Electrochemical transduction via {best.sensor.name}: domain-graph "
                f"recognition-sensor efficiency={efficiency}, upstream recognition "
                f"compatibility={recognition.compatibility_score}."
            ),
            sensitivity=float(perf.sensitivity) if perf and perf.sensitivity is not None else None,
            specificity=float(perf.specificity) if perf and perf.specificity is not None else None,
            lod_value=float(perf.lod_value) if perf and perf.lod_value is not None else None,
            lod_unit=perf.lod_unit if perf else None,
            is_estimated=bool(perf.is_estimated) if perf else None,
            limitations=(
                []
                if perf is not None
                else [
                    "No sensor_performances record exists for this sensor — sensitivity/"
                    "specificity/LOD are unset, not zero."
                ]
            )
            + [
                "Research use only — experimental (wet-lab) validation is required before "
                "any performance claim is relied upon."
            ],
            supporting_evidence=recognition.supporting_evidence,
        )
