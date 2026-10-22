"""Composition root: the one place that knows every concrete class.

Builds adapters from settings and wires them into the service. Nothing here opens a network
connection (httpx and the Gemini client connect lazily), so a misconfigured dependency is
caught by settings validation at startup and by the first request otherwise. `aclose` releases
what was created.
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

import httpx
from google import genai

from app.adapters.db.memory_repository import InMemoryAssessmentRepository
from app.adapters.gemini.advisor import GeminiAdvisoryGenerator
from app.adapters.storage.memory import InMemoryImageStore
from app.adapters.storage.s3 import S3ImageStore, create_s3_client
from app.adapters.vision_client.client import HttpVisionDetector
from app.core.clock import SystemClock
from app.core.config import AssessmentStoreBackend, ImageStoreBackend, Settings
from app.core.ids import new_assessment_id
from app.domain.errors import InvariantViolationError
from app.domain.taxonomy import ECX_TAXONOMY
from app.services.assessment_service import AssessmentService
from app.services.image_validation import ImageLimits
from app.services.ports import AssessmentRepository, ImageStore


@dataclass(slots=True)
class Container:
    service: AssessmentService
    _closers: list[Callable[[], Awaitable[None]]] = field(default_factory=list)

    async def aclose(self) -> None:
        for close in reversed(self._closers):
            await close()


def _build_image_store(settings: Settings) -> ImageStore:
    match settings.image_store:
        case ImageStoreBackend.S3:
            if not (settings.s3_bucket and settings.s3_region):  # settings already enforce this
                raise InvariantViolationError("S3 selected without bucket and region")
            endpoint = str(settings.s3_endpoint_url) if settings.s3_endpoint_url else None
            client = create_s3_client(region=settings.s3_region, endpoint_url=endpoint)
            return S3ImageStore(client=client, bucket=settings.s3_bucket)
        case ImageStoreBackend.MEMORY:
            return InMemoryImageStore()


def _build_repository(settings: Settings) -> AssessmentRepository:
    match settings.assessment_store:
        case AssessmentStoreBackend.MEMORY:
            return InMemoryAssessmentRepository()


def build_container(settings: Settings) -> Container:
    closers: list[Callable[[], Awaitable[None]]] = []

    http = httpx.AsyncClient(
        base_url=str(settings.vision_service_url),
        timeout=httpx.Timeout(settings.vision_timeout_s, connect=settings.vision_connect_timeout_s),
    )
    closers.append(http.aclose)

    gemini_client = genai.Client(api_key=settings.gemini_api_key.get_secret_value())
    closers.append(gemini_client.aio.aclose)

    service = AssessmentService(
        vision=HttpVisionDetector(http=http),
        advisor=GeminiAdvisoryGenerator(
            client=gemini_client,
            model=settings.gemini_model,
            temperature=settings.gemini_temperature,
            timeout_s=settings.gemini_timeout_s,
            max_output_tokens=settings.gemini_max_output_tokens,
        ),
        images=_build_image_store(settings),
        repository=_build_repository(settings),
        taxonomy=ECX_TAXONOMY,
        limits=ImageLimits(
            max_bytes=settings.max_image_bytes,
            max_pixels=settings.max_image_pixels,
            min_side_px=settings.min_image_side_px,
        ),
        clock=SystemClock(),
        new_id=new_assessment_id,
        image_url_ttl_s=settings.image_url_ttl_s,
        retain_original_image=settings.retain_original_image,
    )
    return Container(service=service, _closers=closers)
