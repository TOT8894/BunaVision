"""The assessment workflow.

    validate -> detect (vision) -> map to taxonomy -> summarize -> advise (Gemini)
             -> store images -> persist

This is the only place those steps are sequenced. It depends on ports and domain rules, never
on HTTP, boto3, httpx, or an SDK, so every step can be faked in a unit test.

Failure policy (no fallbacks, no fabricated results):

* Bad input (`ClientInputError`) is rejected before anything runs and is NOT recorded.
* If a dependency fails after we accepted the request, the failure is recorded as a failed
  assessment (status + error code, no result) and the error is re-raised to the caller.
* A partial run never looks like a success: images are written only after every step that can
  fail has succeeded, and are deleted again if the final save fails.
"""

import asyncio
import hashlib
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime

from app.domain.analysis import build_coverage, summarize
from app.domain.errors import (
    AssessmentNotFoundError,
    BunaVisionError,
    DependencyError,
    DuplicateIdempotencyKeyError,
    IdempotencyKeyReusedError,
    PersistenceError,
)
from app.domain.models import Assessment, AssessmentPage, AssessmentResult, Detection
from app.domain.taxonomy import DefectTaxonomy
from app.services.image_validation import ImageLimits, ValidatedImage, validate_image
from app.services.ports import (
    AdvisoryFacts,
    AdvisoryGenerator,
    AssessmentRepository,
    Clock,
    ImageStore,
    VisionDetector,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AssessmentView:
    """An assessment plus short-lived image URLs, valid only for the response that carries them."""

    assessment: Assessment
    original_image_url: str | None
    annotated_image_url: str | None
    image_url_ttl_s: int


@dataclass(frozen=True, slots=True)
class CreateOutcome:
    view: AssessmentView
    created: bool  # False when an idempotent retry returned the earlier result


@dataclass(frozen=True, slots=True)
class _StoredKeys:
    original: str | None
    annotated: str | None

    def present(self) -> list[str]:
        return [key for key in (self.original, self.annotated) if key is not None]


class AssessmentService:
    def __init__(
        self,
        *,
        vision: VisionDetector,
<<<<<<< HEAD
        # advisor: AdvisoryGenerator,
=======
        advisor: AdvisoryGenerator,
>>>>>>> 9a4331aae5c644cfca76c5963eb8630d56a97804
        images: ImageStore,
        repository: AssessmentRepository,
        taxonomy: DefectTaxonomy,
        limits: ImageLimits,
        clock: Clock,
        new_id: Callable[[], str],
        image_url_ttl_s: int,
        retain_original_image: bool,
    ) -> None:
        self._vision = vision
<<<<<<< HEAD
        # self._advisor = advisor
=======
        self._advisor = advisor
>>>>>>> 9a4331aae5c644cfca76c5963eb8630d56a97804
        self._images = images
        self._repository = repository
        self._taxonomy = taxonomy
        self._limits = limits
        self._clock = clock
        self._new_id = new_id
        self._image_url_ttl_s = image_url_ttl_s
        self._retain_original_image = retain_original_image

    @property
    def max_upload_bytes(self) -> int:
        return self._limits.max_bytes

    # --- Use cases ---------------------------------------------------------------------

    async def create_assessment(
        self, *, data: bytes, owner_id: str, idempotency_key: str | None = None
    ) -> CreateOutcome:
        image_sha256 = hashlib.sha256(data).hexdigest()

        if idempotency_key is not None:
            replay = await self._replay(owner_id, idempotency_key, image_sha256)
            if replay is not None:
                return replay

        # Validation errors propagate untouched and are not recorded: nothing was attempted.
        image = await asyncio.to_thread(validate_image, data, self._limits)

        assessment_id = self._new_id()
        created_at = self._clock.now()
        started = self._clock.monotonic()
        try:
            assessment = await self._run_pipeline(
                assessment_id=assessment_id,
                owner_id=owner_id,
                image=image,
                image_sha256=image_sha256,
                idempotency_key=idempotency_key,
                created_at=created_at,
                started=started,
            )
        except DuplicateIdempotencyKeyError as exc:
            # A concurrent request with the same key finished first. Replay its result.
            if idempotency_key is None:
                raise PersistenceError("duplicate key reported for a keyless request") from exc
            replay = await self._replay(owner_id, idempotency_key, image_sha256)
            if replay is None:
                raise PersistenceError("idempotency conflict but no stored assessment") from exc
            return replay
        except DependencyError as exc:
            exc.assessment_id = assessment_id
            await self._record_failure(
                assessment_id=assessment_id,
                owner_id=owner_id,
                created_at=created_at,
                started=started,
                image_sha256=image_sha256,
                error=exc,
            )
            raise
        return CreateOutcome(await self._view(assessment), created=True)

    async def get_assessment(self, *, assessment_id: str, owner_id: str) -> AssessmentView:
        assessment = await self._repository.get(assessment_id, owner_id)
        if assessment is None:
            # Same answer for "does not exist" and "belongs to someone else".
            raise AssessmentNotFoundError(f"assessment {assessment_id} not found for owner")
        return await self._view(assessment)

    async def list_assessments(
        self, *, owner_id: str, limit: int, cursor: str | None
    ) -> AssessmentPage:
        return await self._repository.list_for_owner(owner_id, limit=limit, cursor=cursor)

    # --- Pipeline steps ----------------------------------------------------------------

    async def _replay(
        self, owner_id: str, idempotency_key: str, image_sha256: str
    ) -> CreateOutcome | None:
        earlier = await self._repository.find_by_idempotency_key(owner_id, idempotency_key)
        if earlier is None:
            return None
        if earlier.image_sha256 != image_sha256:
            raise IdempotencyKeyReusedError(
                f"key reused by {owner_id} for a different image (assessment {earlier.assessment_id})"
            )
        return CreateOutcome(await self._view(earlier), created=False)

    async def _run_pipeline(
        self,
        *,
        assessment_id: str,
        owner_id: str,
        image: ValidatedImage,
        image_sha256: str,
        idempotency_key: str | None,
        created_at: datetime,
        started: float,
    ) -> Assessment:
        output = await self._vision.detect(image)

        # Unknown labels and category drift raise here. We never guess a category.
        detections = tuple(
            Detection(
                defect=self._taxonomy.resolve(raw.label, raw.reported_category),
                confidence=raw.confidence,
                box=raw.box,
            )
            for raw in output.detections
        )
        summary = summarize(detections)
        coverage = build_coverage(self._taxonomy)

<<<<<<< HEAD
        # advisory = await self._advisor.generate(
        #     AdvisoryFacts(model_version=output.model_version, summary=summary, coverage=coverage)
        # )
=======
        advisory = await self._advisor.generate(
            AdvisoryFacts(model_version=output.model_version, summary=summary, coverage=coverage)
        )
>>>>>>> 9a4331aae5c644cfca76c5963eb8630d56a97804

        keys = await self._store_images(assessment_id, image, output.annotated_image)
        assessment = Assessment.completed(
            assessment_id=assessment_id,
            owner_id=owner_id,
            created_at=created_at,
            processing_time_ms=self._elapsed_ms(started),
            image_sha256=image_sha256,
            idempotency_key=idempotency_key,
            result=AssessmentResult(
                model_version=output.model_version,
                detections=detections,
                summary=summary,
                coverage=coverage,
<<<<<<< HEAD
                # advisory=advisory,
=======
                advisory=advisory,
>>>>>>> 9a4331aae5c644cfca76c5963eb8630d56a97804
                original_image_key=keys.original,
                annotated_image_key=keys.annotated,
            ),
        )
        try:
            await self._repository.add(assessment)
        except BunaVisionError:
            await self._discard_images(keys.present())
            raise
        return assessment

    async def _store_images(
        self, assessment_id: str, image: ValidatedImage, annotated: bytes | None
    ) -> _StoredKeys:
        stored: list[str] = []
        original_key: str | None = None
        annotated_key: str | None = None
        try:
            if self._retain_original_image:
                original_key = f"assessments/{assessment_id}/original.{image.format.extension}"
                await self._images.put(original_key, image.data, image.format.content_type)
                stored.append(original_key)
            if annotated is not None:
                annotated_key = f"assessments/{assessment_id}/annotated.jpg"
                await self._images.put(annotated_key, annotated, "image/jpeg")
                stored.append(annotated_key)
        except BunaVisionError:
            await self._discard_images(stored)
            raise
        return _StoredKeys(original=original_key, annotated=annotated_key)

    async def _discard_images(self, keys: Sequence[str]) -> None:
        """Best-effort cleanup while another error is already propagating.

        Swallowing a cleanup failure here is deliberate: the caller is about to re-raise the
        error that mattered, and a second exception would hide it. The leak is logged.
        """
        if not keys:
            return
        try:
            await self._images.delete(keys)
        except BunaVisionError:
            logger.warning("could not delete orphaned images %s", list(keys), exc_info=True)

    async def _record_failure(
        self,
        *,
        assessment_id: str,
        owner_id: str,
        created_at: datetime,
        started: float,
        image_sha256: str,
        error: BunaVisionError,
    ) -> None:
        logger.warning("assessment %s failed: %s (%s)", assessment_id, error.code, error)
        failed = Assessment.failed(
            assessment_id=assessment_id,
            owner_id=owner_id,
            created_at=created_at,
            processing_time_ms=self._elapsed_ms(started),
            image_sha256=image_sha256,
            error_code=error.code,
        )
        try:
            await self._repository.add(failed)
        except BunaVisionError:
            # Same reasoning as `_discard_images`: never mask the original failure.
            logger.error("could not record failed assessment %s", assessment_id, exc_info=True)

    # --- Helpers -----------------------------------------------------------------------

    async def _view(self, assessment: Assessment) -> AssessmentView:
        result = assessment.result
        return AssessmentView(
            assessment=assessment,
            original_image_url=await self._url(result.original_image_key if result else None),
            annotated_image_url=await self._url(result.annotated_image_key if result else None),
            image_url_ttl_s=self._image_url_ttl_s,
        )

    async def _url(self, key: str | None) -> str | None:
        return None if key is None else await self._images.url_for(key, self._image_url_ttl_s)

    def _elapsed_ms(self, started: float) -> int:
        return int((self._clock.monotonic() - started) * 1000)
