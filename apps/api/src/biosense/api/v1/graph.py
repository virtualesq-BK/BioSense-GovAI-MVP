from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from biosense.api.dependencies import get_db_session
from biosense.application.dto.ingestion import (
    GraphSyncDomainResponse,
    GraphSyncGeneRequest,
    GraphSyncGeneResponse,
)
from biosense.application.services.knowledge_graph_sync_service import KnowledgeGraphSyncService
from biosense.infrastructure.external.gdc_client import GdcClient

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


@router.post("/sync/schema")
async def sync_schema(session: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    service = KnowledgeGraphSyncService(session)
    await service.ensure_schema()
    return {"message": "Neo4j schema constraints ensured"}


@router.post("/sync/domain", response_model=GraphSyncDomainResponse)
async def sync_domain_graph(
    session: AsyncSession = Depends(get_db_session),
) -> GraphSyncDomainResponse:
    """Push the existing Postgres Cancer→Biomarker→Recognition→Sensor graph into Neo4j."""
    service = KnowledgeGraphSyncService(session)
    counts = await service.sync_domain_graph()
    await session.commit()
    return GraphSyncDomainResponse(
        **counts,
        message=(
            f"Synced {counts['cancers']} cancers, {counts['biomarkers']} biomarkers, "
            f"{counts['sensors']} sensors, {counts['publications']} publication links"
        ),
    )


@router.post("/sync/gene", response_model=GraphSyncGeneResponse)
async def sync_gene_from_gdc(
    body: GraphSyncGeneRequest,
    session: AsyncSession = Depends(get_db_session),
) -> GraphSyncGeneResponse:
    """Fetch a gene + its mutations from NCI GDC (open-access) and sync into Neo4j."""
    gdc = GdcClient()
    service = KnowledgeGraphSyncService(session)

    genes = await gdc.search_genes(body.symbol)
    for gene in genes:
        await service.sync_gene(gene)

    mutations = await gdc.search_mutations(gene_symbol=body.symbol)
    for mutation in mutations:
        await service.sync_mutation(mutation)
    await session.commit()

    return GraphSyncGeneResponse(
        gene_symbol=body.symbol.upper(),
        mutations_synced=len(mutations),
        message=f"Synced {len(genes)} gene(s) and {len(mutations)} mutation(s) from GDC",
    )
