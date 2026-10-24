"""Operator use cases, mapped to the administrator stories in spec section 5.3:

* "processing failures recorded"  -> `list_assessments(status=failed, ...)`
* "model versions recorded"       -> `model_version_usage()`
* "upload and inference limits"   -> `operational_limits()` (enforced in `AssessmentService`)

plus asking the vision service to reload its model. Authorization (admin only) is enforced by
the API layer before any of these are called; nothing here reads user input beyond filters.
"""

import logging
from datetime import timedelta

from app.domain.errors import AssessmentNotFoundError, ErrorCode
from app.domain.models import Assessment, AssessmentPage, AssessmentStatus
from app.domain.operations import (
    ModelReloadResult,
    ModelVersionUsage,
    OperationalLimits,
    OutcomeOverview,
)
from app.services.ports import AssessmentAdminQueries, Clock, VisionAdmin

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(
        self,
        *,
        queries: AssessmentAdminQueries,
        vision_admin: VisionAdmin,
        limits: OperationalLimits,
        clock: Clock,
    ) -> None:
        self._queries = queries
        self._vision_admin = vision_admin
        self._limits = limits
        self._clock = clock

    async def list_assessments(
        self,
        *,
        status: AssessmentStatus | None,
        error_code: ErrorCode | None,
        owner_id: str | None,
        limit: int,
        cursor: str | None,
    ) -> AssessmentPage:
        return await self._queries.list_all(
            status=status, error_code=error_code, owner_id=owner_id, limit=limit, cursor=cursor
        )

    async def get_assessment(self, assessment_id: str) -> Assessment:
        assessment = await self._queries.get_any(assessment_id)
        if assessment is None:
            raise AssessmentNotFoundError(f"assessment {assessment_id} not found")
        return assessment

    async def model_version_usage(self) -> tuple[ModelVersionUsage, ...]:
        return await self._queries.model_version_usage()

    async def outcome_overview(self, *, window_hours: int) -> OutcomeOverview:
        since = self._clock.now() - timedelta(hours=window_hours)
        outcomes = await self._queries.outcome_counts(since)
        return OutcomeOverview(since=since, window_hours=window_hours, outcomes=outcomes)

    def operational_limits(self) -> OperationalLimits:
        return self._limits

    async def reload_vision_model(self, *, actor_id: str) -> ModelReloadResult:
        # Audit trail: who asked, and how it ended. Failures raise ModelReloadFailedError.
        logger.info("admin %s requested a vision model reload", actor_id)
        result = await self._vision_admin.reload_model()
        logger.info("vision model reload by admin %s finished: reloaded=%s", actor_id, result.reloaded)
        return result
