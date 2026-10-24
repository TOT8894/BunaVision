"""Composition root: the one place that knows which concrete adapter implements each port.

Everything else depends on ports. Swapping the image store, database, or vision transport is a
change here and nowhere else. Resources opened here are closed here, in reverse order, when the
application shuts down or if startup fails part-way.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

import httpx
from google import genai
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.db.postgres.assessment_repository import PostgresAssessmentRepository
from app.adapters.db.postgres.engine import create_engine, create_session_factory, verify_schema
from app.adapters.db.postgres.user_repository import PostgresUserRepository
from app.adapters.gemini.advisor import GeminiAdvisoryGenerator
from app.adapters.security.passwords import ScryptPasswordHasher
from app.adapters.security.tokens import JwtTokenIssuer
from app.adapters.storage.memory import InMemoryImageStore
from app.adapters.storage.s3 import S3ImageStore, create_s3_client
from app.adapters.vision_client.client import HttpVisionAdmin, HttpVisionDetector
from app.core.clock import SystemClock
from app.core.config import ConfigurationError, ImageStoreBackend, Settings
from app.core.ids import new_assessment_id, new_user_id
from app.domain.operations import OperationalLimits
from app.domain.taxonomy import ECX_TAXONOMY
from app.services.admin_service import AdminService
from app.services.assessment_service import AssessmentService
from app.services.auth_service import AuthService
from app.services.bundle import Services
from app.services.image_validation import ImageLimits
from app.services.ports import Clock, ImageStore, UserRepository

logger = logging.getLogger(__name__)


def build_image_store(settings: Settings) -> ImageStore:
    match settings.image_store:
        case ImageStoreBackend.MEMORY:
            logger.warning("IMAGE_STORE=memory: images are lost on restart and URLs are not fetchable")
            return InMemoryImageStore()
        case ImageStoreBackend.S3:
            if settings.s3_bucket is None or settings.s3_region is None:
                raise ConfigurationError("S3_BUCKET and S3_REGION are required when IMAGE_STORE=s3")
            endpoint = None if settings.s3_endpoint_url is None else str(settings.s3_endpoint_url)
            return S3ImageStore(
                client=create_s3_client(region=settings.s3_region, endpoint_url=endpoint),
                bucket=settings.s3_bucket,
            )


def build_auth_service(settings: Settings, users: UserRepository, clock: Clock) -> AuthService:
    """Shared with `scripts/create_admin.py` so the script and the API hash and sign identically."""
    return AuthService(
        users=users,
        hasher=ScryptPasswordHasher(),
        tokens=JwtTokenIssuer(
            secret=settings.jwt_secret.get_secret_value(),
            ttl_s=settings.access_token_ttl_s,
            clock=clock,
        ),
        clock=clock,
        new_id=new_user_id,
    )


@asynccontextmanager
async def build_services(settings: Settings) -> AsyncIterator[Services]:
    async with AsyncExitStack() as stack:
        clock = SystemClock()

        engine = create_engine(
            url=settings.database_url.get_secret_value(),
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
        )
        stack.push_async_callback(engine.dispose)
        await verify_schema(engine)  # fail now, with a clear message, not on the first request
        sessions: async_sessionmaker[AsyncSession] = create_session_factory(engine)
        assessments_repo = PostgresAssessmentRepository(sessions, ECX_TAXONOMY)
        users_repo = PostgresUserRepository(sessions)

        vision_http = await stack.enter_async_context(
            httpx.AsyncClient(
                base_url=str(settings.vision_service_url),
                timeout=httpx.Timeout(
                    settings.vision_timeout_s, connect=settings.vision_connect_timeout_s
                ),
            )
        )
        genai_client = genai.Client(api_key=settings.gemini_api_key.get_secret_value())
        stack.callback(genai_client.close)  # runs second (last in, first out)
        stack.push_async_callback(genai_client.aio.aclose)  # runs first

        assessments = AssessmentService(
            vision=HttpVisionDetector(http=vision_http),
            advisor=GeminiAdvisoryGenerator(
                client=genai_client,
                model=settings.gemini_model,
                temperature=settings.gemini_temperature,
                timeout_s=settings.gemini_timeout_s,
                max_output_tokens=settings.gemini_max_output_tokens,
            ),
            images=build_image_store(settings),
            repository=assessments_repo,
            taxonomy=ECX_TAXONOMY,
            limits=ImageLimits(
                max_bytes=settings.max_image_bytes,
                max_pixels=settings.max_image_pixels,
                min_side_px=settings.min_image_side_px,
            ),
            clock=clock,
            new_id=new_assessment_id,
            image_url_ttl_s=settings.image_url_ttl_s,
            retain_original_image=settings.retain_original_image,
            max_assessments_per_hour=settings.max_assessments_per_user_per_hour,
            max_concurrent_assessments=settings.max_concurrent_assessments,
        )
        admin = AdminService(
            queries=assessments_repo,
            vision_admin=HttpVisionAdmin(
                http=vision_http, timeout_s=settings.vision_reload_timeout_s
            ),
            limits=OperationalLimits(
                max_image_bytes=settings.max_image_bytes,
                max_image_pixels=settings.max_image_pixels,
                min_image_side_px=settings.min_image_side_px,
                max_assessments_per_user_per_hour=settings.max_assessments_per_user_per_hour,
                max_concurrent_assessments=settings.max_concurrent_assessments,
                vision_timeout_s=settings.vision_timeout_s,
                gemini_timeout_s=settings.gemini_timeout_s,
                image_url_ttl_s=settings.image_url_ttl_s,
                retain_original_image=settings.retain_original_image,
            ),
            clock=clock,
        )
        yield Services(
            assessments=assessments,
            auth=build_auth_service(settings, users_repo, clock),
            admin=admin,
        )
