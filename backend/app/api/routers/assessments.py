"""Assessment routes. HTTP in, HTTP out: parse the request, call the service, map the result.

No business logic, no boto3/httpx, no error-response building (see `error_handlers`).
"""

from typing import Annotated

from fastapi import APIRouter, File, Header, Query, Response, UploadFile, status

from app.api.dependencies import PrincipalDep, ServiceDep
from app.api.mappers import to_assessment_out, to_completed_out, to_list_out
from app.api.uploads import read_upload
from app.schemas.assessments import AssessmentListOut, AssessmentOut, CompletedAssessmentOut
from app.schemas.errors import ErrorResponse

router = APIRouter(prefix="/assessments", tags=["Assessments"])

_ERRORS: dict[int | str, dict[str, object]] = {
    status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: {"model": ErrorResponse},
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {"model": ErrorResponse},
    status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ErrorResponse},
    status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    status.HTTP_504_GATEWAY_TIMEOUT: {"model": ErrorResponse},
}


@router.post(
    "",
    response_model=CompletedAssessmentOut,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_200_OK: {"model": CompletedAssessmentOut}, **_ERRORS},
    summary="Create an assessment from a green coffee sample photo",
    description=(
        "Runs the full workflow synchronously. Returns 201 for a new assessment. Send an "
        "`Idempotency-Key` header to make retries safe: the same key with the same image "
        "returns the original result with 200; the same key with a different image is a 409. "
        "A failure after the request was accepted is recorded as a failed assessment and the "
        "error response carries its `assessment_id`."
    ),
)

async def create_assessment(
    response: Response,
    service: ServiceDep,
    principal: PrincipalDep,
    file: Annotated[UploadFile, File(description="JPEG, PNG or WEBP photo of the sample.")],
    idempotency_key: Annotated[
        str | None,
        Header(
            alias="Idempotency-Key",
            min_length=1,
            max_length=128,
            pattern=r"^[A-Za-z0-9._:-]+$",
            description="Client-chosen unique key, e.g. a UUID, reused when retrying.",
        ),
    ] = None,
) -> CompletedAssessmentOut:

    data = await read_upload(file, service.max_upload_bytes)
    outcome = await service.create_assessment(
        data=data, owner_id=principal.user_id, idempotency_key=idempotency_key
    )
    body = to_completed_out(outcome.view)
    if outcome.created:
        response.headers["Location"] = f"/api/v1/assessments/{body.assessment_id}"
    else:
        response.status_code = status.HTTP_200_OK
    return body


@router.get(
    "",
    response_model=AssessmentListOut,
    responses=_ERRORS,
    summary="List your assessments, newest first",
)
async def list_assessments(
    service: ServiceDep,
    principal: PrincipalDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query(max_length=512, description="From `next_cursor`.")] = None,
) -> AssessmentListOut:

    page = await service.list_assessments(owner_id=principal.user_id, limit=limit, cursor=cursor)
    return to_list_out(page)


@router.get(
    "/{assessment_id}",
    response_model=AssessmentOut,
    responses=_ERRORS,
    summary="Get one assessment (completed or failed), with fresh image URLs",
)
async def get_assessment(
    assessment_id: str, service: ServiceDep, principal: PrincipalDep
) -> AssessmentOut:
    view = await service.get_assessment(assessment_id=assessment_id, owner_id=principal.user_id)
    return to_assessment_out(view)
