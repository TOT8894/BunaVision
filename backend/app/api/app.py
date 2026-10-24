"""The application factory.

`create_app` takes the settings and a "services builder", so tests can swap in fake services
without touching HTTP code. It reads nothing at import time; the process entry point is
`uvicorn app.main:create_app --factory`.
"""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.error_handlers import register_error_handlers
from app.api.middleware import RequestContextMiddleware, RequestSizeLimitMiddleware
from app.api.routers import admin, assessments, auth, health
from app.container import build_services
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.services.bundle import Services

ServicesBuilder = Callable[[Settings], AbstractAsyncContextManager[Services]]

# Room for multipart boundaries and headers on top of the largest allowed image.
_MULTIPART_OVERHEAD_BYTES = 64 * 1024


def create_app(
    settings: Settings | None = None, *, services_builder: ServicesBuilder = build_services
) -> FastAPI:
    if settings is None:
        settings = get_settings()
    active = settings  # a non-optional name for the closures below

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(active.log_level)
        async with services_builder(active) as services:
            app.state.services = services
            yield

    app = FastAPI(
        title="BunaVision API",
        description=(
            "Preliminary AI screening of green coffee sample photos. Results are model "
            "predictions, not official grades."
        ),
        version=__version__,
        lifespan=lifespan,
    )

    # Middleware added first is innermost. CORS goes last so even error responses carry its headers.
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_body_bytes=active.max_image_bytes + _MULTIPART_OVERHEAD_BYTES,
    )
    app.add_middleware(RequestContextMiddleware)
    if active.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=active.cors_allowed_origins,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
            expose_headers=["X-Request-ID"],
            allow_credentials=False,  # tokens travel in the Authorization header, not cookies
        )

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(assessments.router)
    app.include_router(admin.router)
    return app
