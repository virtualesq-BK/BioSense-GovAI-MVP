"""Extract quantitative sensor metrics from paper chunks → sensor_performances."""

from __future__ import annotations

import json
import re
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.config import settings
from biosense.domain.entities.literature import ExtractedMetric
from biosense.infrastructure.ai.openai_client import (
    create_json_chat_completion,
    create_openai_client,
)
from biosense.infrastructure.persistence.postgres.literature_repository import LiteratureRepository

logger = structlog.get_logger()

METRIC_EXTRACTION_SYSTEM = """You extract quantitative biosensor assay metrics from scientific text.
Return valid JSON only with this shape:
{"metrics":[{
  "sensitivity": 0.0-1.0 or null,
  "specificity": 0.0-1.0 or null,
  "auc": 0.0-1.0 or null,
  "lod_value": number or null,
  "lod_unit": "ng/mL"|"pM"|"fM"|"nM"|null,
  "assay_time_minutes": number or null,
  "sample_volume": number or null,
  "sample_volume_unit": "µL"|"uL"|"mL"|null,
  "estimated_cost_usd": number or null,
  "sensor_name_hint": string or null,
  "sensor_type_hint": "electrochemical"|"optical"|"fet"|"lateral_flow"|"microfluidic"|"piezoelectric"|null,
  "extraction_confidence": 0.0-1.0,
  "source_excerpt": "short quote"
}]}
Convert percentages like 92% to 0.92. If uncertain, lower confidence. Omit invented values."""

# Candidate sentence detectors (group name → compiled regex)
_CANDIDATE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "sensitivity",
        re.compile(
            r"(?i)(?:sensitivity|sens\.?)\s*(?:of|was|=|:)?\s*"
            r"(\d{1,3}(?:\.\d+)?)\s*%"
        ),
    ),
    (
        "specificity",
        re.compile(
            r"(?i)(?:specificity|spec\.?)\s*(?:of|was|=|:)?\s*"
            r"(\d{1,3}(?:\.\d+)?)\s*%"
        ),
    ),
    (
        "auc",
        re.compile(
            r"(?i)\bAUC\b\s*(?:of|was|=|:)?\s*(0?\.\d+|1(?:\.0+)?|\d\.\d+)"
        ),
    ),
    (
        "lod",
        re.compile(
            r"(?i)(?:LOD|limit of detection|detection limit)"
            r"(?:\s*\([^)]*\))?"
            r"\s*(?:of|was|=|:)?\s*"
            r"(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*"
            r"(ng/?mL|pg/?mL|µg/?mL|ug/?mL|fM|pM|nM|µM|uM|aM)"
        ),
    ),
    (
        "assay_time",
        re.compile(
            r"(?i)(?:assay time|detection time|turnaround time|"
            r"completed within|within|in)\s*"
            r"(?:of|was|=|:)?\s*"
            r"(\d+(?:\.\d+)?)\s*(min(?:utes?)?|hours?|h)\b"
        ),
    ),
    (
        "sample_volume",
        re.compile(
            r"(?i)(?:sample volume|using|with)\s*"
            r"(?:of|was|=|:)?\s*"
            r"(\d+(?:\.\d+)?)\s*(µL|uL|μL|mL)\b"
        ),
    ),
    (
        "cost",
        re.compile(
            r"(?i)(?:cost|price|USD|\$)\s*(?:of|was|=|:)?\s*"
            r"\$?\s*(\d+(?:\.\d+)?)"
        ),
    ),
]

_SENSOR_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "electrochemical": ("electrochemical", "electrode", "voltammetr", "amperometr", "impedanc"),
    "optical": ("spr", "surface plasmon", "optical", "fluorescence"),
    "SERS": ("sers", "raman", "surface-enhanced raman"),
    "AI_NGS": ("ai-ngs", "ai ngs", "ngs classifier", "sequencing panel"),
    "CRISPR_dedicated": ("crispr sensor", "cas12 cartridge", "cas13 cartridge"),
    "fet": ("fet", "field-effect", "graphene", "transistor"),
    "field_effect_transistor": ("fet", "field-effect", "graphene", "transistor"),
    "lateral_flow": ("lateral flow", "lfa", "paper-based"),
    "microfluidic": ("microfluidic", "lab-on-a-chip", "loc"),
    "piezoelectric": ("qcm", "piezoelectric", "quartz crystal"),
}


class MetricExtractionService:
    """Regex candidates → LLM structured metrics → upsert sensor_performances."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = LiteratureRepository(session)
        self._client = create_openai_client()

    async def extract_for_paper(self, paper_id: UUID) -> list[ExtractedMetric]:
        chunks = await self._repo.list_paper_chunk_texts(paper_id)
        if not chunks:
            logger.info("metric_extraction_no_chunks", paper_id=str(paper_id))
            return []

        candidates = find_metric_candidate_sentences(chunks)
        if not candidates:
            logger.info("metric_extraction_no_candidates", paper_id=str(paper_id))
            return []

        metrics = await self._refine_with_llm(candidates)
        if not metrics:
            metrics = [parse_metric_from_sentence(s) for s in candidates]
            metrics = [m for m in metrics if _has_any_metric(m)]

        sensors = await self._repo.list_sensors()
        stored = 0
        for metric in metrics:
            sensor_id = resolve_sensor_id(metric, sensors, " ".join(candidates))
            if sensor_id is None:
                logger.warning(
                    "metric_extraction_sensor_unresolved",
                    hint=metric.sensor_type_hint or metric.sensor_name_hint,
                )
                continue
            await self._repo.upsert_extracted_performance(
                sensor_id=sensor_id,
                paper_id=paper_id,
                metric=metric,
            )
            stored += 1

        await self._session.commit()
        logger.info(
            "metric_extraction_complete",
            paper_id=str(paper_id),
            candidates=len(candidates),
            metrics=len(metrics),
            stored=stored,
        )
        return metrics

    async def _refine_with_llm(self, sentences: list[str]) -> list[ExtractedMetric]:
        if self._client is None:
            return [m for s in sentences if _has_any_metric(m := parse_metric_from_sentence(s))]

        joined = "\n".join(f"- {s}" for s in sentences[:12])
        try:
            response = await create_json_chat_completion(
                self._client,
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": METRIC_EXTRACTION_SYSTEM},
                    {
                        "role": "user",
                        "content": f"Extract metrics from these candidate sentences:\n{joined}",
                    },
                ],
                temperature=0.1,
            )
            raw = response.choices[0].message.content or "{}"
            return parse_llm_metrics_json(raw)
        except Exception as exc:
            logger.error("metric_extraction_llm_failed", error=str(exc))
            return [m for s in sentences if _has_any_metric(m := parse_metric_from_sentence(s))]


def find_metric_candidate_sentences(chunks: list[str]) -> list[str]:
    """1차: 정규식 기반 후보 문장 탐지."""
    found: list[str] = []
    seen: set[str] = set()
    for chunk in chunks:
        for sentence in _split_sentences(chunk):
            cleaned = " ".join(sentence.split())
            if len(cleaned) < 20 or cleaned in seen:
                continue
            if any(pat.search(cleaned) for _, pat in _CANDIDATE_PATTERNS):
                seen.add(cleaned)
                found.append(cleaned)
    return found


def parse_metric_from_sentence(sentence: str) -> ExtractedMetric:
    """규칙 기반 단일 문장 파싱 (LLM fallback / unit tests)."""
    sens = _match_percent(sentence, "sensitivity")
    spec = _match_percent(sentence, "specificity")
    auc = _match_auc(sentence)
    lod_value, lod_unit = _match_lod(sentence)
    assay_time = _match_assay_time(sentence)
    sample_vol, sample_unit = _match_sample_volume(sentence)
    cost = _match_cost(sentence)
    sensor_type = _infer_sensor_type(sentence)

    filled = sum(
        1
        for v in (sens, spec, auc, lod_value, assay_time, sample_vol, cost)
        if v is not None
    )
    confidence = min(0.55 + 0.08 * filled, 0.85)

    return ExtractedMetric(
        sensitivity=sens,
        specificity=spec,
        auc=auc,
        lod_value=lod_value,
        lod_unit=lod_unit,
        assay_time_minutes=assay_time,
        sample_volume=sample_vol,
        sample_volume_unit=sample_unit,
        estimated_cost_usd=cost,
        sensor_type_hint=sensor_type,
        extraction_confidence=round(confidence, 4),
        source_excerpt=sentence[:280],
        is_estimated=False,
    )


def parse_llm_metrics_json(raw: str) -> list[ExtractedMetric]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    items = data.get("metrics", data if isinstance(data, list) else [data])
    if not isinstance(items, list):
        return []

    metrics: list[ExtractedMetric] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        metric = ExtractedMetric(
            sensitivity=_clamp01(_as_float(item.get("sensitivity"))),
            specificity=_clamp01(_as_float(item.get("specificity"))),
            auc=_clamp01(_as_float(item.get("auc"))),
            lod_value=_as_float(item.get("lod_value")),
            lod_unit=_as_str(item.get("lod_unit")),
            assay_time_minutes=_as_float(item.get("assay_time_minutes")),
            sample_volume=_as_float(item.get("sample_volume")),
            sample_volume_unit=_as_str(item.get("sample_volume_unit")),
            estimated_cost_usd=_as_float(item.get("estimated_cost_usd")),
            sensor_name_hint=_as_str(item.get("sensor_name_hint")),
            sensor_type_hint=_as_str(item.get("sensor_type_hint")),
            extraction_confidence=_clamp01(_as_float(item.get("extraction_confidence")) or 0.6)
            or 0.6,
            source_excerpt=(_as_str(item.get("source_excerpt")) or "")[:280],
            is_estimated=False,
        )
        if _has_any_metric(metric):
            metrics.append(metric)
    return metrics


def resolve_sensor_id(
    metric: ExtractedMetric,
    sensors: list[dict],
    context_text: str,
) -> UUID | None:
    """Map LLM/regex hints to a known sensor UUID."""
    if not sensors:
        return None

    hint_type = (metric.sensor_type_hint or "").lower()
    hint_name = (metric.sensor_name_hint or "").lower()
    ctx = context_text.lower()

    # Exact / substring name match
    if hint_name:
        for s in sensors:
            if hint_name in s["name"].lower() or s["name"].lower() in hint_name:
                return s["id"]

    # Type match
    type_key = hint_type or _infer_sensor_type(ctx) or ""
    if type_key:
        for s in sensors:
            if s["sensor_type"].lower() == type_key:
                return s["id"]
            if type_key in s["name"].lower() or type_key in s["sensor_type"].lower():
                return s["id"]

    # Keyword fallback on sensor catalog
    for sensor_type, keywords in _SENSOR_TYPE_KEYWORDS.items():
        if any(k in ctx for k in keywords):
            for s in sensors:
                if s["sensor_type"].lower() == sensor_type:
                    return s["id"]

    return sensors[0]["id"] if sensors else None


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def _match_percent(sentence: str, kind: str) -> float | None:
    for name, pat in _CANDIDATE_PATTERNS:
        if name != kind:
            continue
        m = pat.search(sentence)
        if not m:
            return None
        value = float(m.group(1))
        if value > 1.0:
            value = value / 100.0
        return _clamp01(value)
    return None


def _match_auc(sentence: str) -> float | None:
    m = _CANDIDATE_PATTERNS[2][1].search(sentence)
    if not m:
        return None
    return _clamp01(float(m.group(1)))


def _match_lod(sentence: str) -> tuple[float | None, str | None]:
    m = _CANDIDATE_PATTERNS[3][1].search(sentence)
    if not m:
        return None, None
    unit = m.group(2).replace("ug", "µg").replace("μ", "µ")
    if unit.lower() in {"ng/ml", "ngml"}:
        unit = "ng/mL"
    return float(m.group(1)), unit


def _match_assay_time(sentence: str) -> float | None:
    m = _CANDIDATE_PATTERNS[4][1].search(sentence)
    if not m:
        return None
    value = float(m.group(1))
    unit = m.group(2).lower()
    if unit.startswith("h"):
        return value * 60.0
    return value


def _match_sample_volume(sentence: str) -> tuple[float | None, str | None]:
    m = _CANDIDATE_PATTERNS[5][1].search(sentence)
    if not m:
        return None, None
    unit = m.group(2).replace("μL", "µL").replace("uL", "µL")
    return float(m.group(1)), unit


def _match_cost(sentence: str) -> float | None:
    m = _CANDIDATE_PATTERNS[6][1].search(sentence)
    if not m:
        return None
    return float(m.group(1))


def _infer_sensor_type(text: str) -> str | None:
    lowered = text.lower()
    for sensor_type, keywords in _SENSOR_TYPE_KEYWORDS.items():
        if any(k in lowered for k in keywords):
            return sensor_type
    return None


def _has_any_metric(metric: ExtractedMetric) -> bool:
    return any(
        v is not None
        for v in (
            metric.sensitivity,
            metric.specificity,
            metric.auc,
            metric.lod_value,
            metric.assay_time_minutes,
            metric.sample_volume,
            metric.estimated_cost_usd,
        )
    )


def _as_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _as_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clamp01(value: float | None) -> float | None:
    if value is None:
        return None
    return round(min(max(value, 0.0), 1.0), 4)
