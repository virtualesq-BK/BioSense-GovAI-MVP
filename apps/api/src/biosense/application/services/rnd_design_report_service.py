"""Biomarker-Sensor Co-Design Engine: assembles the structured R&D Design Report.

Pipeline (§13):
    Cancer -> Population Evidence -> Biomarker Candidates -> Molecular Characteristics
    -> Recognition Mechanism -> Sensor Candidates -> Performance Evidence
    -> Ranked Recommendation

Every section is built from a real query (Postgres domain graph, live GDC, or the
Biomarker Priority Score) — nothing here is a made-up number. Sections with no
underlying evidence are left empty/None and surfaced in `data_limitations`, not
silently defaulted.
"""

from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from biosense.application.services.biomarker_priority_service import BiomarkerPriorityService
from biosense.application.services.feature_extraction_service import FeatureExtractionService
from biosense.application.services.graph_retrieval_service import (
    GraphRetrievalService,
    PublicHealthFeatureService,
)
from biosense.domain.entities.recommendation import GraphCandidate, RecommendationInput
from biosense.domain.entities.rnd_report import (
    EpidemiologicalEvidence,
    ExperimentalDesignHypothesis,
    MolecularCharacteristics,
    ReferenceEntry,
    RndDesignInput,
    RndDesignReport,
    SensorCandidate,
)
from biosense.domain.services.normalization import (
    normalize_cancer_type,
    normalize_country,
    normalize_gene_symbol,
)
from biosense.infrastructure.external.gdc_client import GdcClient
from biosense.infrastructure.persistence.postgres.models import (
    Biomarker,
    Cancer,
    CancerBiomarker,
    SensorPerformance,
)

logger = structlog.get_logger()

_STANDARD_LIMITATIONS: tuple[str, ...] = (
    "For research support only — not a medical diagnosis.",
    "Not a substitute for clinical decision-making.",
    "AI-generated recommendations require experimental (wet-lab) validation before use.",
    "Controlled-access genomic data (e.g. dbGaP-gated GDC records) is not accessed by "
    "this platform; only open-access molecular metadata is used.",
)


class RndDesignReportService:
    def __init__(self, session: AsyncSession, *, gdc: GdcClient | None = None) -> None:
        self._session = session
        self._public_health = PublicHealthFeatureService(session)
        self._graph = GraphRetrievalService(session)
        self._priority = BiomarkerPriorityService(session, gdc=gdc)
        self._features = FeatureExtractionService()
        self._gdc = gdc or GdcClient()

    async def generate(self, inp: RndDesignInput) -> RndDesignReport:
        country_code = normalize_country(inp.country)
        cancer_code = normalize_cancer_type(inp.cancer)

        cancer = (
            await self._session.execute(select(Cancer).where(Cancer.code == cancer_code))
        ).scalar_one_or_none()

        epi = await self._build_epidemiology(cancer, inp.region_code)

        candidates = await self._select_biomarker_candidates(cancer_code, inp)
        top = candidates[0] if candidates else None

        molecular = await self._build_molecular_characteristics(cancer_code, top)

        sensor_candidates: list[SensorCandidate] = []
        recognition_strategy: str | None = None
        experimental_hypothesis: ExperimentalDesignHypothesis | None = None
        existing_evidence: list[ReferenceEntry] = []

        if top is not None and cancer is not None:
            biomarker_row = await self._load_biomarker(top.biomarker_name)
            ctdna_class = biomarker_row.ctdna.code if biomarker_row and biomarker_row.ctdna else (
                inp.biomarker_type or ""
            )
            graph_candidates = await self._retrieve_sensor_candidates(
                cancer_code=cancer_code,
                ctdna_class=ctdna_class,
                region_code=inp.region_code,
                patient_age=inp.patient_age,
                biomarker_name=top.biomarker_name,
                epi=epi,
            )
            sensor_candidates = [
                await self._to_sensor_candidate(c) for c in graph_candidates
            ]
            if sensor_candidates:
                recognition_strategy = sensor_candidates[0].recognition_code
            if biomarker_row:
                existing_evidence = [
                    ReferenceEntry(external_id=p.external_id, title=p.title, source=p.source)
                    for p in biomarker_row.papers
                ]
                if graph_candidates:
                    best = graph_candidates[0]
                    protocol_steps = best.protocol_steps
                    experimental_hypothesis = ExperimentalDesignHypothesis(
                        steps=protocol_steps
                        or [
                            "AI-suggested starting point (not experimentally validated):",
                            "Prepare sample and extract target biomarker",
                            f"Immobilize {best.recognition_name} recognition element "
                            "on sensor surface",
                            "Incubate with target and measure signal",
                            "Validate against negative controls",
                        ],
                        reagents=[best.recognition_name, "buffer", "wash solution"],
                        duration_hours=6.0 if not protocol_steps else None,
                        is_ai_suggested=not bool(protocol_steps),
                    )

        expected_performance = sensor_candidates[0] if sensor_candidates else None
        evidence_confidence = top.total_score if top else 0.0

        limitations = list(_STANDARD_LIMITATIONS)
        if top is None:
            limitations.append(
                f"No biomarker candidates found in the domain graph for cancer="
                f"'{cancer_code}'"
                + (f", biomarker_type='{inp.biomarker_type}'" if inp.biomarker_type else "")
                + (f", target_gene='{inp.target_gene}'" if inp.target_gene else "")
                + ". This report's epidemiology section still reflects real data; the "
                "molecular/sensor sections cannot be populated."
            )
        else:
            for factor in top.missing_data_factors:
                limitations.append(f"Missing evidence for '{factor}' on {top.biomarker_name}.")
        if expected_performance is not None and expected_performance.is_estimated:
            limitations.append(
                "Expected performance is a literature-derived estimate, not a direct "
                "experimental measurement — verify before relying on it."
            )
        if expected_performance is not None and expected_performance.is_estimated is None:
            limitations.append(
                "No sensor performance record exists for the top candidate — sensitivity/"
                "specificity/LOD fields are unset, not zero."
            )

        references = [f"{e.source}:{e.external_id} — {e.title}" for e in existing_evidence]
        if molecular.gene_symbol:
            references.append(f"NCI GDC gene record: {molecular.gene_symbol}")

        logger.info(
            "rnd_design_report_generated",
            country=country_code,
            cancer=cancer_code,
            biomarker=top.biomarker_name if top else None,
        )

        return RndDesignReport(
            target_disease=cancer.name_en if cancer else inp.cancer,
            goal=inp.goal,
            epidemiological_evidence=epi,
            biomarker_candidates=candidates,
            selected_biomarker_name=top.biomarker_name if top else None,
            molecular_characteristics=molecular,
            recognition_strategy=recognition_strategy,
            sensor_candidates=sensor_candidates,
            existing_evidence=existing_evidence,
            expected_performance=expected_performance,
            evidence_confidence=evidence_confidence,
            experimental_design_hypothesis=experimental_hypothesis,
            data_limitations=limitations,
            references=references,
        )

    async def _build_epidemiology(
        self, cancer: Cancer | None, region_code: str
    ) -> EpidemiologicalEvidence:
        if cancer is None:
            return EpidemiologicalEvidence(
                region_code=region_code,
                region_name_ko=None,
                incidence_rate=None,
                mortality_rate=None,
                national_incidence_avg=None,
                national_mortality_avg=None,
                narrative="",
                source="none",
                missing_data=True,
            )
        snapshot = await self._public_health.fetch_features(cancer.code, region_code)
        missing = snapshot.incidence_rate is None and snapshot.mortality_rate is None
        return EpidemiologicalEvidence(
            region_code=snapshot.region_code,
            region_name_ko=snapshot.region_name_ko,
            incidence_rate=snapshot.incidence_rate,
            mortality_rate=snapshot.mortality_rate,
            national_incidence_avg=snapshot.national_incidence_avg,
            national_mortality_avg=snapshot.national_mortality_avg,
            narrative="",
            source="KOSIS/KDCA" if not missing else "none",
            missing_data=missing,
        )

    async def _select_biomarker_candidates(self, cancer_code: str, inp: RndDesignInput) -> list:
        candidates = await self._priority.score_biomarkers_for_cancer(cancer_code)
        if not candidates:
            return []

        if inp.biomarker_type or inp.target_gene:
            allowed_names = await self._filter_biomarker_names(
                cancer_code, inp.biomarker_type, inp.target_gene
            )
            candidates = [c for c in candidates if c.biomarker_name in allowed_names]
        return candidates

    async def _filter_biomarker_names(
        self, cancer_code: str, ctdna_class: str | None, target_gene: str | None
    ) -> set[str]:
        query = (
            select(Biomarker)
            .join(CancerBiomarker, CancerBiomarker.biomarker_id == Biomarker.id)
            .join(Cancer, Cancer.id == CancerBiomarker.cancer_id)
            .where(Cancer.code == cancer_code)
            .options(selectinload(Biomarker.ctdna))
        )
        rows = (await self._session.execute(query)).scalars().unique().all()

        names: set[str] = set()
        target_symbol = normalize_gene_symbol(target_gene) if target_gene else None
        for row in rows:
            if ctdna_class and (not row.ctdna or row.ctdna.code != ctdna_class):
                continue
            if target_symbol and normalize_gene_symbol(row.gene_symbol or "") != target_symbol:
                continue
            names.add(row.name)
        return names

    async def _load_biomarker(self, name: str) -> Biomarker | None:
        return (
            await self._session.execute(
                select(Biomarker)
                .where(Biomarker.name == name)
                .options(selectinload(Biomarker.ctdna), selectinload(Biomarker.papers))
            )
        ).scalars().unique().one_or_none()

    async def _build_molecular_characteristics(
        self, cancer_code: str, top
    ) -> MolecularCharacteristics:
        if top is None:
            return MolecularCharacteristics(
                gene_symbol=None,
                gene_name=None,
                biotype=None,
                mutation_count=None,
                source="none",
                missing_data=True,
            )
        biomarker_row = await self._load_biomarker(top.biomarker_name)
        gene_symbol = biomarker_row.gene_symbol if biomarker_row else None
        if not gene_symbol:
            return MolecularCharacteristics(
                gene_symbol=None,
                gene_name=None,
                biotype=None,
                mutation_count=None,
                source="none",
                missing_data=True,
            )

        genes = await self._gdc.search_genes(gene_symbol)
        mutation_count = await self._gdc.count_mutations_for_gene(gene_symbol)
        gene = genes[0] if genes else None
        return MolecularCharacteristics(
            gene_symbol=normalize_gene_symbol(gene_symbol),
            gene_name=gene.name if gene else None,
            biotype=gene.biotype if gene else None,
            mutation_count=mutation_count,
            source="NCI GDC",
            missing_data=gene is None and mutation_count is None,
        )

    async def _retrieve_sensor_candidates(
        self,
        *,
        cancer_code: str,
        ctdna_class: str,
        region_code: str,
        patient_age: int,
        biomarker_name: str,
        epi: EpidemiologicalEvidence,
    ) -> list[GraphCandidate]:
        rec_input = RecommendationInput(
            cancer_type=cancer_code,
            ctdna_class=ctdna_class,
            region_code=region_code,
            patient_age=patient_age,
            biomarker_name=biomarker_name,
        )
        features = self._features.extract(
            rec_input,
            incidence_rate=epi.incidence_rate,
            mortality_rate=epi.mortality_rate,
            national_incidence_avg=epi.national_incidence_avg,
            national_mortality_avg=epi.national_mortality_avg,
            region_name_ko=epi.region_name_ko,
        )
        return await self._graph.retrieve_candidates(features, limit=5)

    async def _to_sensor_candidate(self, c: GraphCandidate) -> SensorCandidate:
        is_estimated: bool | None = None
        if c.sensitivity is not None or c.specificity is not None or c.lod_value is not None:
            perf = await self._session.execute(
                select(SensorPerformance.is_estimated)
                .where(SensorPerformance.sensor_id == c.sensor_id)
                .order_by(SensorPerformance.sensitivity.desc().nulls_last())
                .limit(1)
            )
            row = perf.scalar_one_or_none()
            is_estimated = bool(row) if row is not None else None

        return SensorCandidate(
            sensor_name=c.sensor_name,
            sensor_type=c.sensor_type,
            recognition_code=c.recognition_code,
            recognition_name=c.recognition_name,
            match_score=c.match_score,
            sensor_efficiency=c.sensor_efficiency,
            sensitivity=c.sensitivity,
            specificity=c.specificity,
            lod_value=c.lod_value,
            lod_unit=c.lod_unit,
            estimated_cost_usd=c.estimated_cost_usd,
            is_estimated=is_estimated,
            graph_path=c.graph_path,
        )
