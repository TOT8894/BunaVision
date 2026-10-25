"""FastAPI dependencies: the services, and who the caller is."""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.errors import AuthenticationRequiredError, ForbiddenError
from app.domain.users import Role, User
from app.services.admin_service import AdminService
from app.services.assessment_service import AssessmentService
from app.services.auth_service import AuthService
from app.services.bundle import Services

# auto_error=False: a missing header must produce OUR error envelope, not FastAPI's default.
_bearer = HTTPBearer(auto_error=False, description="Access token from POST /api/v1/auth/login")


def get_services(request: Request) -> Services:
    services: Services = request.app.state.services
    return services


ServicesDep = Annotated[Services, Depends(get_services)]


def get_assessment_service(services: ServicesDep) -> AssessmentService:
    return services.assessments


def get_auth_service(services: ServicesDep) -> AuthService:
    return services.auth


def get_admin_service(services: ServicesDep) -> AdminService:
    return services.admin


AssessmentServiceDep = Annotated[AssessmentService, Depends(get_assessment_service)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    auth: AuthServiceDep,
) -> User:
    if credentials is None:
        raise AuthenticationRequiredError("no bearer token on the request")
    return await auth.authenticate(credentials.credentials)


CurrentUserDep = Annotated[User, Depends(get_current_user)]


async def require_admin(user: CurrentUserDep) -> User:
    if user.role is not Role.ADMIN:
        raise ForbiddenError(f"user {user.user_id} attempted an admin action")
    return user


AdminUserDep = Annotated[User, Depends(require_admin)]
