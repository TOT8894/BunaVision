"""Administrator API (spec section 5.3). Every route needs `is_staff`; admins are created with
`createsuperuser` or by ticking is_staff in the Django admin site, never over HTTP."""

import logging
from datetime import timedelta

from django.conf import settings
from django.db.models import Count, Max, Min
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.assessments.clients import vision
from apps.assessments.models import Assessment
from apps.assessments.serializers import (
    AdminAssessmentSerializer,
    AdminFilterSerializer,
    LimitsSerializer,
    ModelReloadSerializer,
    ModelVersionsSerializer,
    OverviewQuerySerializer,
    OverviewSerializer,
)
from apps.common.errors import AssessmentNotFound
from apps.common.pagination import NewestFirstCursorPagination
from apps.common.serializers import errors

logger = logging.getLogger(__name__)


class _AdminView(APIView):
    permission_classes = [IsAdminUser]


class AdminAssessmentListView(_AdminView):
    @extend_schema(
        summary="Every user's assessments, newest first (status=failed to troubleshoot)",
        parameters=[AdminFilterSerializer],
        responses={200: AdminAssessmentSerializer(many=True), **errors(401, 403, 422)},
    )
    def get(self, request):  # noqa: ANN001, ANN201
        filters = AdminFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        queryset = Assessment.objects.all()
        if "status" in filters.validated_data:
            queryset = queryset.filter(status=filters.validated_data["status"])
        if "error_code" in filters.validated_data:
            queryset = queryset.filter(error_code=filters.validated_data["error_code"])
        if "owner_id" in filters.validated_data:
            queryset = queryset.filter(owner_id=filters.validated_data["owner_id"])
        paginator = NewestFirstCursorPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(AdminAssessmentSerializer(page, many=True).data)


class AdminAssessmentDetailView(_AdminView):
    @extend_schema(summary="One recorded attempt, from any user", responses={200: AdminAssessmentSerializer, **errors(401, 403, 404)})
    def get(self, request, assessment_id: str):  # noqa: ANN001, ANN201
        assessment = Assessment.objects.filter(id=assessment_id).first()
        if assessment is None:
            raise AssessmentNotFound(f"assessment {assessment_id} not found")
        return Response(AdminAssessmentSerializer(assessment).data)


class AdminModelVersionsView(_AdminView):
    @extend_schema(summary="Vision model and validator versions that produced results", responses={200: ModelVersionsSerializer, **errors(401, 403)})
    def get(self, request):  # noqa: ANN001, ANN201
        versions = (
            Assessment.objects.filter(status=Assessment.Status.COMPLETED)
            .values("model_version", "validator_version")
            .annotate(assessments=Count("id"), first_seen=Min("created_at"), last_seen=Max("created_at"))
            .order_by("-last_seen")
        )
        return Response({"versions": list(versions)})


class AdminOverviewView(_AdminView):
    @extend_schema(
        summary="Outcome counts: completed, and failed by error code",
        parameters=[OverviewQuerySerializer],
        responses={200: OverviewSerializer, **errors(401, 403, 422)},
    )
    def get(self, request):  # noqa: ANN001, ANN201
        query = OverviewQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        hours = query.validated_data["window_hours"]
        since = timezone.now() - timedelta(hours=hours)
        outcomes = (
            Assessment.objects.filter(created_at__gte=since)
            .values("status", "error_code")
            .annotate(count=Count("id"))
            .order_by("-count", "status")
        )
        return Response({"since": since, "window_hours": hours, "outcomes": list(outcomes)})


class AdminLimitsView(_AdminView):
    @extend_schema(summary="The limits the service enforces (change them through configuration)", responses={200: LimitsSerializer, **errors(401, 403)})
    def get(self, request):  # noqa: ANN001, ANN201
        return Response(
            {
                "max_image_bytes": settings.MAX_IMAGE_BYTES,
                "max_image_pixels": settings.MAX_IMAGE_PIXELS,
                "min_image_side_px": settings.MIN_IMAGE_SIDE_PX,
                "max_assessments_per_user_per_hour": settings.MAX_ASSESSMENTS_PER_USER_PER_HOUR,
                "max_concurrent_assessments": settings.MAX_CONCURRENT_ASSESSMENTS,
                "vision_timeout_s": settings.VISION_TIMEOUT_S,
                "gemini_timeout_s": settings.GEMINI_TIMEOUT_S,
                "image_url_ttl_s": settings.IMAGE_URL_TTL_S,
                "retain_original_image": settings.RETAIN_ORIGINAL_IMAGE,
            }
        )


class AdminReloadModelView(_AdminView):
    @extend_schema(summary="Ask the vision service to reload its model", request=None, responses={200: ModelReloadSerializer, **errors(401, 403, 502)})
    def post(self, request):  # noqa: ANN001, ANN201
        logger.info("admin %s requested a vision model reload", request.user.pk)  # audit trail
        result = vision.reload_model()
        logger.info("vision model reload by admin %s finished: %s", request.user.pk, result)
        return Response(result)
