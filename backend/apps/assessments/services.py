"""The assessment pipeline, in one place.

    replay check -> validate image -> vision -> taxonomy -> summary -> Gemini -> store images -> save

No DB transaction is held while vision or Gemini run (ATOMIC_REQUESTS is off); only the final
insert is atomic. Failure policy, with no fallbacks and no fabricated results:

* Bad input and rejected photos (`ClientError`) are raised untouched and NOT recorded.
* A `DependencyError` after the request was accepted is recorded as a failed assessment, then
  re-raised.
* Images are written only after every step that can fail has succeeded, and deleted again if the
  row cannot be saved.
* A retry with the same Idempotency-Key gets the stored result only if it carries the same image.
"""

import hashlib
import logging
import time
import uuid
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import DatabaseError, IntegrityError, transaction
from django.utils import timezone

from apps.assessments import analysis
from apps.assessments.clients import advisor, vision
from apps.assessments.image_validation import ImageLimits, ValidatedImage, validate_image
from apps.assessments.models import Assessment
from apps.assessments.taxonomy import TAXONOMY, UnknownDefectLabel
from apps.common.errors import (
    DependencyError,
    IdempotencyKeyReused,
    PersistenceFailed,
    UnknownDefectClass,
)

logger = logging.getLogger(__name__)
RESULT_SCHEMA_VERSION = 1


class _IdempotencyLost(Exception):
    """Internal: another request with the same key committed first."""


def create_assessment(*, user: Any, data: bytes, idempotency_key: str | None) -> tuple[Assessment, bool]:
    """Returns (assessment, created). `created` is False for an idempotent replay."""
    image_sha256 = hashlib.sha256(data).hexdigest()
    if idempotency_key is not None:
        earlier = Assessment.objects.filter(owner=user, idempotency_key=idempotency_key).first()
        if earlier is not None:
            return _replay(earlier, image_sha256), False

    image = validate_image(
        data, ImageLimits(settings.MAX_IMAGE_BYTES, settings.MAX_IMAGE_PIXELS, settings.MIN_IMAGE_SIDE_PX)
    )
    assessment_id = f"asmt_{uuid.uuid4().hex}"
    created_at = timezone.now()
    started = time.monotonic()
    try:
        assessment = _run_pipeline(
            user=user, image=image, assessment_id=assessment_id, created_at=created_at,
            started=started, image_sha256=image_sha256, idempotency_key=idempotency_key,
        )
    except _IdempotencyLost:
        earlier = Assessment.objects.filter(owner=user, idempotency_key=idempotency_key).first()
        if earlier is None:
            raise PersistenceFailed("idempotency conflict but no stored assessment") from None
        return _replay(earlier, image_sha256), False
    except DependencyError as exc:
        exc.assessment_id = assessment_id
        _record_failure(user, assessment_id, created_at, started, image_sha256, exc)
        raise
    return assessment, True


def _run_pipeline(
    *, user: Any, image: ValidatedImage, assessment_id: str, created_at: Any, started: float,
    image_sha256: str, idempotency_key: str | None,
) -> Assessment:
    output = vision.detect(image)
    detections = [
        analysis.Detection(defect=_defect_for(raw.label), confidence=raw.confidence, box=raw.box)
        for raw in output.detections
    ]
    summary = analysis.summarize(detections)
    scanned, not_scanned = TAXONOMY.scanned, TAXONOMY.not_scanned
    advisory = advisor.generate(summary, scanned, not_scanned)

    original_key, annotated_key = _store_images(assessment_id, image, output.annotated_image)
    result = {
        "schema": RESULT_SCHEMA_VERSION,
        "model_version": output.model_version,
        "image_check": {
            "coffee_confidence": output.coffee_confidence,
            "validator_version": output.validator_version,
        },
        "detections": [
            {"defect_key": d.defect.key, "confidence": d.confidence, "box": list(d.box)} for d in detections
        ],
        "coverage": {"scanned": [c.key for c in scanned], "not_scanned": [c.key for c in not_scanned]},
        "advisory": advisory,
        "original_image_key": original_key,
        "annotated_image_key": annotated_key,
    }
    stored = [key for key in (original_key, annotated_key) if key is not None]
    try:
        with transaction.atomic():
            return Assessment.objects.create(
                id=assessment_id, owner=user, status=Assessment.Status.COMPLETED,
                created_at=created_at, processing_time_ms=_elapsed_ms(started),
                image_sha256=image_sha256, idempotency_key=idempotency_key,
                model_version=output.model_version, validator_version=output.validator_version,
                result=result,
            )
    except IntegrityError as exc:
        _discard_images(stored)
        if idempotency_key is not None:
            raise _IdempotencyLost from exc
        raise PersistenceFailed(f"could not save the assessment: {exc!r}") from exc
    except DatabaseError as exc:
        _discard_images(stored)
        raise PersistenceFailed(f"could not save the assessment: {exc!r}") from exc
    except BaseException:
        _discard_images(stored)  # cleanup, then re-raise unchanged (cancellation included)
        raise


def _defect_for(label: str):  # noqa: ANN202
    try:
        return TAXONOMY.from_vision_label(label)
    except UnknownDefectLabel as exc:
        raise UnknownDefectClass(f"vision label {label!r} is not in the defect taxonomy") from exc


def _store_images(assessment_id: str, image: ValidatedImage, annotated: bytes | None) -> tuple[str | None, str | None]:
    stored: list[str] = []
    try:
        original = annotated_key = None
        if settings.RETAIN_ORIGINAL_IMAGE:
            original = default_storage.save(
                f"assessments/{assessment_id}/original.{image.format.extension}", ContentFile(image.data)
            )
            stored.append(original)
        if annotated is not None:
            annotated_key = default_storage.save(f"assessments/{assessment_id}/annotated.jpg", ContentFile(annotated))
            stored.append(annotated_key)
    except Exception as exc:  # storage backends raise many unrelated types; keep the cause
        _discard_images(stored)
        raise PersistenceFailed(f"image storage failed: {exc!r}") from exc
    return original, annotated_key


def _discard_images(keys: list[str]) -> None:
    """Best-effort cleanup while another error is propagating: a second exception would hide it."""
    for key in keys:
        try:
            default_storage.delete(key)
        except Exception:  # noqa: BLE001  (logged; the original error is what matters)
            logger.warning("could not delete orphaned image %s", key, exc_info=True)


def _record_failure(user: Any, assessment_id: str, created_at: Any, started: float, sha: str, error: DependencyError) -> None:
    logger.warning("assessment %s failed: %s (%s)", assessment_id, error.code, error)
    try:
        Assessment.objects.create(
            id=assessment_id, owner=user, status=Assessment.Status.FAILED, created_at=created_at,
            processing_time_ms=_elapsed_ms(started), image_sha256=sha, error_code=error.code,
        )  # a failed attempt never keeps the idempotency key, so a retry runs again
    except DatabaseError:
        logger.error("could not record failed assessment %s", assessment_id, exc_info=True)


def _replay(earlier: Assessment, image_sha256: str) -> Assessment:
    if earlier.image_sha256 != image_sha256:
        raise IdempotencyKeyReused(f"key already used by {earlier.id} with different bytes")
    return earlier


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)
