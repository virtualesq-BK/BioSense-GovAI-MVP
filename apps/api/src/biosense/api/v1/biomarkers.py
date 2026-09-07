"""Phase 2: additive read endpoints for biomarker-dimension evidence discovery."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from biosense.domain.entities.methylation import CANCER_TYPE_TO_TCGA_PROJECTS
from biosense.domain.services.normalization import normalize_cancer_type
from biosense.infrastructure.external.gdc_client import GdcClient

router = APIRouter(prefix="/biomarkers", tags=["Biomarkers"])


class MethylationFileEntry(BaseModel):
    file_id: str
    file_name: str | None
    data_type: str | None
    platform: str | None
    access: str | None
    project_id: str | None
    case_count: int | None
    sample_types: list[str]


class MethylationEvidenceResponse(BaseModel):
    cancer_type: str
    tcga_projects: list[str]
    files: list[MethylationFileEntry]
    note: str = (
        "METADATA-ONLY: file/project-level GDC metadata (platform, access, case "
        "linkage). No CpG-site or beta-value quantitative data is included — the "
        "GDC REST API does not expose it. See docs/data-feasibility-phase2.md."
    )


@router.get("/methylation-evidence", response_model=MethylationEvidenceResponse)
async def methylation_evidence(
    cancer: str = Query(..., description="Cancer type, e.g. 'lung', 'colorectal', 'breast'"),
) -> MethylationEvidenceResponse:
    """GDC methylation file/project-level discovery for a cancer type (Phase 2, Step 1/8).

    Metadata-only — never returns a beta value or CpG-site identifier.
    """
    cancer_code = normalize_cancer_type(cancer)
    projects = CANCER_TYPE_TO_TCGA_PROJECTS.get(cancer_code, [])

    gdc = GdcClient()
    files: list[MethylationFileEntry] = []
    for project_id in projects:
        records = await gdc.search_methylation_files(project_id=project_id)
        files.extend(
            MethylationFileEntry(
                file_id=r.file_id,
                file_name=r.file_name,
                data_type=r.data_type,
                platform=r.platform,
                access=r.access,
                project_id=r.project_id,
                case_count=r.case_count,
                sample_types=r.sample_types,
            )
            for r in records
        )

    return MethylationEvidenceResponse(
        cancer_type=cancer_code,
        tcga_projects=projects,
        files=files,
    )
