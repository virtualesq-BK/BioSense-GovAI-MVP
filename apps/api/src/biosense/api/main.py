from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from biosense.api.v1.router import api_v1_router
from biosense.config import settings
from biosense.infrastructure.common.logging import configure_logging
from biosense.jobs.scheduler import start_scheduler, stop_scheduler

configure_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("biosense_api_starting", env=settings.app_env)
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("biosense_api_stopping")


def create_app() -> FastAPI:
    app = FastAPI(
        title="BioSense-GovAI API",
        version="0.1.0",
        description="AI-powered biomarker–biosensor co-design platform",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router)

    return app


app = create_app()
