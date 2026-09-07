# R&D Scoring Calibration — Status (Phase 2, Step 11)

## Question
Does a real benchmark dataset exist in this repo that could be used to measure
the accuracy of `rd_scoring_service.py`'s 6-factor composite score, or of the
Molecular Recognition Engine's compatibility scores?

## What was checked
- `infra/seed/` — contains only `infra/seed/public_health/` (public-health
  feature seed data used by `biomarker_priority_service.py`'s clinical-relevance
  factor). It is reference/lookup data, not a labeled benchmark of "correct"
  biomarker/recognition/sensor recommendations.
- `apps/api/tests/` — unit and integration tests assert code behavior
  (e.g. "given this mocked GDC response, the service returns X"), not accuracy
  against independently-verified ground truth. No `tests/benchmark` directory
  exists.
- No dataset of expert-curated "gold" biomarker → recognition → sensor
  recommendations, nor any outcome/validation data (e.g. wet-lab results,
  clinical trial outcomes) was found anywhere in the repository.

## Conclusion
**No real benchmark dataset exists in this repo today.** Calibration of the
R&D scoring weights (documented in `rd_scoring_service.py` as "INITIAL
HEURISTIC WEIGHTS — NOT EMPIRICALLY VALIDATED") against real accuracy is
therefore **deferred**. This document does not change the scoring weights and
reports no accuracy numbers, fabricated or otherwise — there is nothing to
measure against yet.

## What calibration would require (Phase 3 scope)
1. A curated set of biomarker/recognition/sensor combinations with an
   independently-sourced "correct" or "preferred" outcome (e.g. from published
   assay validation studies, expert panel review, or wet-lab results produced
   by this platform's own downstream users).
2. A defined accuracy metric (e.g. rank correlation between the composite
   score and the benchmark's preferred ordering) and a held-out evaluation
   split so the weights aren't tuned on the same data used to validate them.
3. A process for keeping the benchmark itself honest — provenance-tracked
   (mirroring the `EvidenceRef` pattern already used elsewhere in this
   codebase), not another set of guessed numbers.

Until that benchmark exists, the 6-factor weights should continue to be
treated and labeled as an initial, non-empirically-validated heuristic
wherever they are surfaced (API responses, UI, docs).
