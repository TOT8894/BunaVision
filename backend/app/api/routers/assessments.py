from typing import Annotated

from fastapi import APIRouter, File, Header, Query, Response, UploadFile, status
from fastapi import Path as PathParam

from app.api.dependencies import AssessmentServiceDep, CurrentUserDep
from app.api.mappers import to_assessment_out, to_completed_out, to_list_out
from app.api.openapi import error_responses
from app.api.uploads import read_upload
from app.schemas.assessments import AssessmentListOut, AssessmentOut, CompletedAssessmentOut

router = APIRouter(prefix="/api/v1/assessments", tags=["assessments"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CompletedAssessmentOut,
    summary="Analyse a green coffee sample photo",
    description=(
        "Needs a signed-in user. Photos that do not show green coffee are rejected with "
        "`IMAGE_NOT_COFFEE` (422); their `error.details.is_coffee` is false. "
        "Send an `Idempotency-Key` header to make retries safe."
    ),
    responses={
        200: {
            "model": CompletedAssessmentOut,
            "description": "An earlier assessment with the same Idempotency-Key and image.",
        },
        **error_responses(400, 401, 413, 415, 422, 429, 502, 503, 504),
    },
)
async def create_assessment(
    image: Annotated[UploadFile, File(description="JPEG, PNG or WEBP photo of the sample.")],
    response: Response,
    service: AssessmentServiceDep,
    user: CurrentUserDep,
    idempotency_key: Annotated[
        str | None,
        Header(
            min_length=1,
            max_length=128,
            description="Any unique string per upload attempt. Reuse it only to retry.",
        ),
    ] = None,
) -> CompletedAssessmentOut:
    data = await read_upload(image, service.max_upload_bytes)
    outcome = await service.create_assessment(
        data=data, owner_id=user.user_id, idempotency_key=idempotency_key
    )
    if not outcome.created:
        response.status_code = status.HTTP_200_OK
    return to_completed_out(outcome.view)


@router.get(
    "",
    response_model=AssessmentListOut,
    summary="Your assessment history, newest first",
    responses=error_responses(401, 422),
)
async def list_assessments(
    service: AssessmentServiceDep,
    user: CurrentUserDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query(max_length=512, description="From `next_cursor`.")] = None,
) -> AssessmentListOut:
    page = await service.list_assessments(owner_id=user.user_id, limit=limit, cursor=cursor)
    return to_list_out(page)


@router.get(
    "/{assessment_id}",
    response_model=AssessmentOut,
    summary="One of your assessments",
    responses=error_responses(401, 404),
)
async def get_assessment(
    assessment_id: Annotated[str, PathParam(min_length=1, max_length=64)],
    service: AssessmentServiceDep,
    user: CurrentUserDep,
) -> AssessmentOut:
    view = await service.get_assessment(assessment_id=assessment_id, owner_id=user.user_id)
    return to_assessment_out(view)
