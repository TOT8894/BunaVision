"""Application factory.

    uvicorn app.main:app_factory --factory --host 0.0.0.0 --port 8000

`create_app` takes the settings explicitly (and optionally a ready-made service), so tests and
the OpenAPI export never touch the real environment or real dependencies.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.error_handlers import register_error_handlers
from app.api.middleware import RequestContextMiddleware, RequestSizeLimitMiddleware
from app.api.routers import assessments, health
from app.container import build_container
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.services.assessment_service import AssessmentService

API_PREFIX = "/api/v1"


def create_app(*, settings: Settings, service: AssessmentService | None = None) -> FastAPI:
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        container = None
        if service is None:
            container = build_container(settings)
            app.state.service = container.service
        try:
            yield
        finally:
            if container is not None:
                await container.aclose()

    app = FastAPI(
        title="BunaVision Backend",
        version=__version__,
        description=(
            "Public API for preliminary AI screening of green coffee samples. Results are "
            "preliminary model predictions, never an official grade."
        ),
        lifespan=lifespan,
    )
    if service is not None:
        app.state.service = service

    register_error_handlers(app)

    # Middleware: the LAST one added is the OUTERMOST. Order outside-in:
    # request context -> CORS -> size limit -> app.
    app.add_middleware(RequestSizeLimitMiddleware, max_body_bytes=settings.max_body_bytes)
    if settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allowed_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "Idempotency-Key", "X-Request-ID"],
            expose_headers=["X-Request-ID", "Location"],
        )
    app.add_middleware(RequestContextMiddleware)

    app.include_router(health.router)
    app.include_router(assessments.router, prefix=API_PREFIX)
    return app


def app_factory() -> FastAPI:
    """Entry point for uvicorn. Reads settings from the environment and fails fast if invalid."""
    return create_app(settings=get_settings())
