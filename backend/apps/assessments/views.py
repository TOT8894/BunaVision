from django.conf import settings
from django.core.files.storage import default_storage
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_field,
)
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.assessments import services
from apps.assessments.models import Assessment
from apps.assessments.presentation import present, present_list_item
from apps.assessments.serializers import (
    CompletedAssessmentSerializer,
    CompletedListItemSerializer,
    FailedAssessmentSerializer,
    FailedListItemSerializer,
    render_assessment,
    render_list_item,
)
from apps.common.errors import AssessmentNotFound, ImageTooLarge, InvalidRequest
from apps.common.pagination import NewestFirstCursorPagination
from apps.common.serializers import errors

_MAX_KEY_LENGTH = 128


_ASSESSMENT = PolymorphicProxySerializer(
    component_name="Assessment",
    serializers=[CompletedAssessmentSerializer, FailedAssessmentSerializer],
    resource_type_field_name="status",
)


class _AssessmentListDocs(serializers.Serializer):
    """Documentation only: the real response is built by the paginator."""

    items = serializers.SerializerMethodField()
    next_cursor = serializers.CharField(allow_null=True)

    @extend_schema_field(
        PolymorphicProxySerializer(
            component_name="AssessmentListItem",
            serializers=[CompletedListItemSerializer, FailedListItemSerializer],
            resource_type_field_name="status",
            many=True,
        )
    )
    def get_items(self, obj):  # noqa: ANN001, ANN201
        raise NotImplementedError


class AssessmentListCreateView(APIView):
    parser_classes = [MultiPartParser]
    throttle_classes = [ScopedRateThrottle]

    @property
    def throttle_scope(self) -> str | None:
        # The hourly quota applies to uploads only, not to reading history.
        request = getattr(self, "request", None)
        return "assessments" if getattr(request, "method", None) == "POST" else None

    @extend_schema(
        summary="Analyse a green coffee sample photo",
        description=(
            "Photos that do not show green coffee are rejected with IMAGE_NOT_COFFEE (422); "
            "`error.details.is_coffee` is false. Send an `Idempotency-Key` header to make retries safe."
        ),
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {"image": {"type": "string", "format": "binary"}},
                "required": ["image"],
            }
        },
        parameters=[OpenApiParameter("Idempotency-Key", OpenApiTypes.STR, OpenApiParameter.HEADER, required=False)],
        responses={201: CompletedAssessmentSerializer, 200: CompletedAssessmentSerializer, **errors(400, 401, 413, 415, 422, 429, 502, 503, 504)},
    )
    def post(self, request):  # noqa: ANN001, ANN201
        image = request.FILES.get("image")
        if image is None:
            raise InvalidRequest("missing image field", public_message="The `image` file field is required.")
        if image.size > settings.MAX_IMAGE_BYTES:
            raise ImageTooLarge(f"{image.size} bytes exceeds {settings.MAX_IMAGE_BYTES}")
        key = request.headers.get("Idempotency-Key")
        if key is not None and not 1 <= len(key) <= _MAX_KEY_LENGTH:
            raise InvalidRequest("bad Idempotency-Key", public_message=f"Idempotency-Key must be 1-{_MAX_KEY_LENGTH} characters.")

        assessment, created = services.create_assessment(user=request.user, data=image.read(), idempotency_key=key)
        return Response(render_assessment(present(assessment, default_storage.url)), status=201 if created else 200)

    @extend_schema(
        summary="Your assessment history, newest first",
        parameters=[
            OpenApiParameter("limit", OpenApiTypes.INT, description="1-100, default 20"),
            OpenApiParameter("cursor", OpenApiTypes.STR, description="From `next_cursor`"),
        ],
        responses={200: _AssessmentListDocs, **errors(401)},
    )
    def get(self, request):  # noqa: ANN001, ANN201
        paginator = NewestFirstCursorPagination()
        page = paginator.paginate_queryset(Assessment.objects.filter(owner=request.user), request, view=self)
        return paginator.get_paginated_response([render_list_item(present_list_item(a)) for a in page])


class AssessmentDetailView(APIView):
    @extend_schema(summary="One of your assessments", responses={200: _ASSESSMENT, **errors(401, 404)})
    def get(self, request, assessment_id: str):  # noqa: ANN001, ANN201
        # Someone else's assessment is indistinguishable from a missing one.
        assessment = Assessment.objects.filter(id=assessment_id, owner=request.user).first()
        if assessment is None:
            raise AssessmentNotFound(f"assessment {assessment_id} not found for user {request.user.pk}")
        return Response(render_assessment(present(assessment, default_storage.url)))


