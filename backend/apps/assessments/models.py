from django.conf import settings
from django.db import models
from django.db.models import Q


class Assessment(models.Model):
    """One accepted upload: either completed (with a result) or failed (with an error code).

    `result` is one JSON document (schema version 1): model/validator versions, detections,
    coverage, advisory and image keys. The summary is not stored; it is recomputed from the
    detections so counts can never disagree with the boxes they came from.
    """

    class Status(models.TextChoices):
        COMPLETED = "completed"
        FAILED = "failed"

    id = models.CharField(primary_key=True, max_length=64)  # asmt_<32 hex>
    # PROTECT: users who own history are deactivated, never deleted.
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assessments")
    status = models.CharField(max_length=16, choices=Status.choices)
    created_at = models.DateTimeField()
    processing_time_ms = models.PositiveIntegerField()
    image_sha256 = models.CharField(max_length=64)
    idempotency_key = models.CharField(max_length=128, null=True, blank=True)
    error_code = models.CharField(max_length=40, null=True, blank=True)
    model_version = models.CharField(max_length=200, null=True, blank=True)
    validator_version = models.CharField(max_length=200, null=True, blank=True)
    result = models.JSONField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "idempotency_key"],
                condition=Q(idempotency_key__isnull=False),
                name="uq_assessment_owner_idempotency",
            ),
            models.CheckConstraint(
                name="ck_assessment_shape",
                condition=(
                    Q(status="completed", result__isnull=False, error_code__isnull=True,
                      model_version__isnull=False, validator_version__isnull=False)
                    | Q(status="failed", result__isnull=True, error_code__isnull=False,
                        model_version__isnull=True, validator_version__isnull=True)
                ),
            ),
        ]
        indexes = [
            models.Index(fields=["owner", "-created_at", "-id"], name="ix_asmt_owner_created"),
            models.Index(fields=["status", "-created_at"], name="ix_asmt_status_created"),
        ]

    def __str__(self) -> str:
        return self.id
