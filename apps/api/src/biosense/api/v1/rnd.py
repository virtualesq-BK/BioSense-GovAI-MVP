from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.api.dependencies import get_db_session
from biosense.application.dto.rnd_report import RndDesignReportResponse, RndDesignRequest
from biosense.application.services.rnd_design_report_service import RndDesignReportService
from biosense.domain.entities.rnd_report import RndDesignInput, RndDesignReport

router = APIRouter(prefix="/rnd", tags=["R&D Design"])


@router.post("/design", response_model=RndDesignReportResponse)
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
    )
