"""FastAPI dependencies: the service, and who the caller is."""

from typing import Annotated

from fastapi import Depends, Request

from app.core.security import Principal
from app.services.assessment_service import AssessmentService

# Placeholder until the authentication mechanism is decided. Replacing `get_principal` is the
# whole change: every service and repository call is already owner-scoped.
_DEMO_PRINCIPAL = Principal(user_id="demo-user")


def get_service(request: Request) -> AssessmentService:
    service: AssessmentService = request.app.state.service
    return service


def get_principal() -> Principal:
    return _DEMO_PRINCIPAL


ServiceDep = Annotated[AssessmentService, Depends(get_service)]
PrincipalDep = Annotated[Principal, Depends(get_principal)]
