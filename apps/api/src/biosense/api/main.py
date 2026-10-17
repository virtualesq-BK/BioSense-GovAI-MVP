from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


def _cors_headers(request: Request) -> dict[str, str]:
    # Responses from the ServerErrorMiddleware bypass CORSMiddleware, so the browser
    # would otherwise report a CORS failure instead of the real 500.
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origin_list:
        return {"access-control-allow-origin": origin, "access-control-allow-credentials": "true"}
    return {}


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

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            method=request.method,
            path=request.url.path,
            error_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers=_cors_headers(request),
        )

    app.include_router(api_v1_router)

    return app


app = create_app()
