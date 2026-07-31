from biosense.domain.entities.recommendation import GraphCandidate, ScoredCandidate


class RankingWeights:
    """Hybrid retrieval weight configuration."""

    graph_match: float = 0.30
    sensor_efficiency: float = 0.20
    literature: float = 0.25
    public_health: float = 0.10
    performance: float = 0.15


class WeightedRanker:
    """Score and rank sensor strategy candidates."""

    def __init__(self, weights: RankingWeights | None = None) -> None:
        self._w = weights or RankingWeights()

    def score_candidate(
        self,
        candidate: GraphCandidate,
        *,
        literature_score: float,
        public_health_score: float,
    ) -> float:
        perf = _performance_score(candidate)
        composite = (
            self._w.graph_match * candidate.match_score
            + self._w.sensor_efficiency * candidate.sensor_efficiency
            + self._w.literature * literature_score
            + self._w.public_health * public_health_score
            + self._w.performance * perf
        )
        return round(min(max(composite, 0.0), 1.0), 4)

    def rank(
        self,
        candidates: list[GraphCandidate],
        literature_scores: dict[str, float],
        public_health_score: float,
        literature_citations: dict[str, list[dict]] | None = None,
    ) -> list[ScoredCandidate]:
        citations_map = literature_citations or {}
        scored: list[ScoredCandidate] = []

        for candidate in candidates:
            key = f"{candidate.sensor_id}:{candidate.recognition_id}"
            lit_score = literature_scores.get(key, literature_scores.get(candidate.sensor_id, 0.0))
            composite = self.score_candidate(
                candidate,
                literature_score=lit_score,
                public_health_score=public_health_score,
            )
            confidence = ConfidenceScorer.compute(
                candidate, literature_score=lit_score, composite_score=composite
            )
            scored.append(
                ScoredCandidate(
                    candidate=candidate,
                    literature_score=lit_score,
                    composite_score=composite,
                    confidence=confidence,
                    literature_citations=citations_map.get(key, []),
                )
            )

        scored.sort(key=lambda s: s.composite_score, reverse=True)
        return scored


class ConfidenceScorer:
    """Derive confidence from evidence breadth and score consistency."""

    @staticmethod
    def compute(
        candidate: GraphCandidate,
        *,
        literature_score: float,
        composite_score: float,
    ) -> float:
        evidence_signals = [
            candidate.match_score,
            candidate.sensor_efficiency,
            literature_score,
            1.0 if candidate.sensitivity else 0.3,
            1.0 if candidate.protocol_steps else 0.2,
        ]
        avg_evidence = sum(evidence_signals) / len(evidence_signals)
        confidence = 0.6 * composite_score + 0.4 * avg_evidence
        return round(min(max(confidence, 0.0), 1.0), 4)


def _performance_score(candidate: GraphCandidate) -> float:
    parts: list[float] = []
    if candidate.sensitivity is not None:
        parts.append(candidate.sensitivity)
    if candidate.specificity is not None:
        parts.append(candidate.specificity)
    if candidate.lod_value is not None:
        parts.append(min(1.0, 1.0 / (1.0 + candidate.lod_value)))
    return sum(parts) / len(parts) if parts else 0.5
