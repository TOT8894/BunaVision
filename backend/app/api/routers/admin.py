"""Administrator endpoints (spec section 5.3). Every route requires the `admin` role."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi import Path as PathParam

from app.api.dependencies import AdminServiceDep, AdminUserDep, require_admin
from app.api.mappers import (
    to_admin_assessment_out,
    to_admin_list_out,
    to_limits_out,
    to_model_reload_out,
    to_model_versions_out,
    to_overview_out,
)
from app.api.openapi import error_responses
from app.domain.errors import ErrorCode
from app.domain.models import AssessmentStatus
from app.schemas.admin import (
    AdminAssessmentListOut,
    AdminAssessmentOut,
    LimitsOut,
    ModelReloadOut,
    ModelVersionsOut,
    OverviewOut,
)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
    responses=error_responses(401, 403),
)


@router.get(
    "/assessments",
    response_model=AdminAssessmentListOut,
    summary="Every user's assessments, newest first (use status=failed to troubleshoot)",
    responses=error_responses(422),
)
async def list_assessments(
    service: AdminServiceDep,
    status: AssessmentStatus | None = None,
    error_code: ErrorCode | None = None,
    owner_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query(max_length=512)] = None,
) -> AdminAssessmentListOut:
    page = await service.list_assessments(
        status=status,
        error_code=error_code,
        owner_id=None if owner_id is None else str(owner_id),
        limit=limit,
        cursor=cursor,
    )
    return to_admin_list_out(page)


@router.get(
    "/assessments/{assessment_id}",
    response_model=AdminAssessmentOut,
    summary="One recorded attempt, from any user",
    responses=error_responses(404),
)
async def get_assessment(
    assessment_id: Annotated[str, PathParam(min_length=1, max_length=64)],
    service: AdminServiceDep,
) -> AdminAssessmentOut:
    return to_admin_assessment_out(await service.get_assessment(assessment_id))


@router.get(
    "/model-versions",
    response_model=ModelVersionsOut,
    summary="Which vision model and validator versions produced results, and when",
)
async def model_versions(service: AdminServiceDep) -> ModelVersionsOut:
    return to_model_versions_out(await service.model_version_usage())


@router.get(
    "/overview",
    response_model=OverviewOut,
    summary="Outcome counts (completed, and failed by error code) over a time window",
    responses=error_responses(422),
)
async def overview(
    service: AdminServiceDep,
    window_hours: Annotated[int, Query(ge=1, le=720)] = 24,
) -> OverviewOut:
    return to_overview_out(await service.outcome_overview(window_hours=window_hours))


@router.get(
    "/limits",
    response_model=LimitsOut,
    summary="The upload, quota and timeout limits the service enforces",
)
async def limits(service: AdminServiceDep) -> LimitsOut:
    return to_limits_out(service.operational_limits())


@router.post(
    "/vision/reload-model",
    response_model=ModelReloadOut,
    summary="Ask the vision service to reload its model",
    responses=error_responses(502),
)
async def reload_vision_model(service: AdminServiceDep, admin: AdminUserDep) -> ModelReloadOut:
    return to_model_reload_out(await service.reload_vision_model(actor_id=admin.user_id))
