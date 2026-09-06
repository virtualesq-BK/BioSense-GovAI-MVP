from fastapi import APIRouter

from biosense.api.v1 import catalog, graph, health, ingestion, literature, recommendations, users

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(health.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(ingestion.router)
api_v1_router.include_router(literature.router)
api_v1_router.include_router(recommendations.router)
api_v1_router.include_router(graph.router)
api_v1_router.include_router(catalog.router)
