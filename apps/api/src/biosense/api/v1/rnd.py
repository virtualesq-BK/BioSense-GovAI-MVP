from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.api.dependencies import get_db_session, rate_limit_expensive
from biosense.application.dto.rnd_report import (
    DetectabilityResponse,
    MolecularCharacterizationResponse,
    MolecularDetectabilityResponse,
    RdCompositeScoreResponse,
    RdScoreFactorResponse,
    RecognitionRecommendationResponse,
    RndDesignReportResponse,
    RndDesignRequest,
    SensorTransductionCandidateResponse,
)
from biosense.application.services.rnd_design_report_service import RndDesignReportService
from biosense.domain.entities.molecular_characterization import MolecularCharacterizationResult
from biosense.domain.entities.molecular_detectability import MolecularDetectabilityResult
from biosense.domain.entities.molecular_recognition import RecognitionRecommendation
from biosense.domain.entities.rd_scoring import RdCompositeScore
from biosense.domain.entities.rnd_report import RndDesignInput, RndDesignReport
from biosense.domain.entities.sensor_transduction import SensorTransductionCandidate

router = APIRouter(prefix="/rnd", tags=["R&D Design"])


@router.post(
    "/design",
    response_model=RndDesignReportResponse,
    dependencies=[Depends(rate_limit_expensive)],
)
async def design_report(
    body: RndDesignRequest,
    session: AsyncSession = Depends(get_db_session),
) -> RndDesignReportResponse:
    """Biomarker-Sensor Co-Design Engine (§13): generates a structured R&D report.

    Example: "lung cancer, mutation-class ctDNA, early detection" -> ranked
    biomarker candidates, molecular characteristics (live GDC), recognition
    strategy, ranked sensor candidates with real (not fabricated) performance
    data where it exists, and explicit data-limitation callouts.
    """
    service = RndDesignReportService(session)
    report = await service.generate(
        RndDesignInput(
            country=body.country,
            cancer=body.cancer,
            biomarker_type=body.biomarker_type,
            target_gene=body.target_gene,
            goal=body.goal,
            region_code=body.region_code,
            patient_age=body.patient_age,
        )
    )
    return _to_response(report)


def _to_response(report: RndDesignReport) -> RndDesignReportResponse:
    return RndDesignReportResponse(
        target_disease=report.target_disease,
        goal=report.goal,
        epidemiological_evidence=report.epidemiological_evidence,
        biomarker_candidates=report.biomarker_candidates,
        selected_biomarker_name=report.selected_biomarker_name,
        molecular_characteristics=report.molecular_characteristics,
        recognition_strategy=report.recognition_strategy,
        sensor_candidates=report.sensor_candidates,
        existing_evidence=report.existing_evidence,
        expected_performance=report.expected_performance,
        evidence_confidence=report.evidence_confidence,
        experimental_design_hypothesis=report.experimental_design_hypothesis,
        data_limitations=report.data_limitations,
        references=report.references,
        phase1_molecular_characterization=_to_molecular_characterization_response(
            report.phase1_molecular_characterization
        ),
        phase1_detectability=_to_detectability_response(report.phase1_detectability),
        phase1_recognition_recommendations=[
            _to_recognition_response(r) for r in report.phase1_recognition_recommendations
        ],
        phase1_sensor_transduction_candidates=[
            _to_sensor_transduction_response(s)
            for s in report.phase1_sensor_transduction_candidates
        ],
        phase1_composite_score=_to_composite_score_response(report.phase1_composite_score),
        phase1_disclaimers=report.phase1_disclaimers,
    )


def _to_molecular_characterization_response(
    mc: MolecularCharacterizationResult | None,
) -> MolecularCharacterizationResponse | None:
    if mc is None:
        return None
    return MolecularCharacterizationResponse(
        biomarker=mc.biomarker,
        dimension=mc.dimension,
        molecular_characteristics=mc.molecular_characteristics,
        detectability=(
            DetectabilityResponse(
                is_detectable_in_ctdna=mc.detectability.is_detectable_in_ctdna,
                mutation_count=mc.detectability.mutation_count,
                basis=mc.detectability.basis,
                missing_data=mc.detectability.missing_data,
            )
            if mc.detectability is not None
            else None
        ),
        specificity_features=mc.specificity_features,
        limitations=mc.limitations,
        evidence=[
            {
                "source": e.source,
                "external_id": e.external_id,
                "title": e.title,
                "dataset": e.dataset,
                "original_identifier": e.original_identifier,
                "access_date": e.access_date,
                "access_level": e.access_level,
                "evidence_type": e.evidence_type,
            }
            for e in mc.evidence
        ],
        evidence_status=mc.evidence_status.value,
        evidence_status_reason=mc.evidence_status_reason,
    )


def _to_detectability_response(
    d: MolecularDetectabilityResult | None,
) -> MolecularDetectabilityResponse | None:
    if d is None:
        return None
    return MolecularDetectabilityResponse(
        biomarker=d.biomarker,
        dimension=d.dimension,
        abundance=d.abundance,
        allele_fraction=d.allele_fraction,
        sequence_specificity=d.sequence_specificity,
        chemical_distinguishability=d.chemical_distinguishability,
        structural_signal=d.structural_signal,
        sample_compatibility=d.sample_compatibility,
        background_interference=d.background_interference,
        detectability_confidence=d.detectability_confidence,
        basis=d.basis,
        evidence=[
            {"source": e.source, "external_id": e.external_id, "title": e.title}
            for e in d.evidence
        ],
        limitations=d.limitations,
    )


def _to_recognition_response(r: RecognitionRecommendation) -> RecognitionRecommendationResponse:
    return RecognitionRecommendationResponse(
        strategy=r.strategy.value,
        status=r.status,
        compatibility_score=r.compatibility_score,
        rationale=r.rationale,
        supporting_evidence=r.supporting_evidence,
        limitations=r.limitations,
        confidence=r.confidence,
        computation_basis=r.computation_basis,
        evidence_source=r.evidence_source,
        citation_evidence=[
            {
                "source": e.source,
                "external_id": e.external_id,
                "title": e.title,
                "original_identifier": e.original_identifier,
                "access_date": e.access_date,
                "evidence_type": e.evidence_type,
            }
            for e in r.citation_evidence
        ],
    )


def _to_sensor_transduction_response(
    s: SensorTransductionCandidate,
) -> SensorTransductionCandidateResponse:
    return SensorTransductionCandidateResponse(
        platform=s.platform.value,
        status=s.status,
        sensor_name=s.sensor_name,
        feasibility_score=s.feasibility_score,
        rationale=s.rationale,
        sensitivity=s.sensitivity,
        specificity=s.specificity,
        lod_value=s.lod_value,
        lod_unit=s.lod_unit,
        is_estimated=s.is_estimated,
        limitations=s.limitations,
        supporting_evidence=s.supporting_evidence,
    )


def _to_composite_score_response(score: RdCompositeScore | None) -> RdCompositeScoreResponse | None:
    if score is None:
        return None
    return RdCompositeScoreResponse(
        biomarker_name=score.biomarker_name,
        molecular_fit=RdScoreFactorResponse(**vars(score.molecular_fit)),
        recognition_feasibility=RdScoreFactorResponse(**vars(score.recognition_feasibility)),
        sensor_feasibility=RdScoreFactorResponse(**vars(score.sensor_feasibility)),
        published_evidence=RdScoreFactorResponse(**vars(score.published_evidence)),
        clinical_relevance=RdScoreFactorResponse(**vars(score.clinical_relevance)),
        data_confidence=RdScoreFactorResponse(**vars(score.data_confidence)),
        weights=score.weights,
        total_score=score.total_score,
    )
