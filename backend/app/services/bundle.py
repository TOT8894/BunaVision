"""The services the API needs, built once at startup by the container."""

from dataclasses import dataclass

from app.services.admin_service import AdminService
from app.services.assessment_service import AssessmentService
from app.services.auth_service import AuthService


@dataclass(frozen=True, slots=True)
class Services:
    assessments: AssessmentService
    auth: AuthService
    admin: AdminService
