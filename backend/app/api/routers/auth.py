from fastapi import APIRouter, status

from app.api.dependencies import AuthServiceDep, CurrentUserDep
from app.api.mappers import to_token_out, to_user_out
from app.api.openapi import error_responses
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserOut,
    summary="Create an account",
    responses=error_responses(409, 422),
)
async def register(body: RegisterIn, auth: AuthServiceDep) -> UserOut:
    return to_user_out(await auth.register(email=body.email, password=body.password))


@router.post(
    "/login",
    response_model=TokenOut,
    summary="Exchange email and password for an access token",
    responses=error_responses(401, 422),
)
async def login(body: LoginIn, auth: AuthServiceDep) -> TokenOut:
    return to_token_out(await auth.login(email=body.email, password=body.password))


@router.get(
    "/me",
    response_model=UserOut,
    summary="The signed-in user",
    responses=error_responses(401),
)
async def me(user: CurrentUserDep) -> UserOut:
    return to_user_out(user)
