"""Response shapes. They render the dicts from `presentation.py` and feed the OpenAPI schema,
so the contract lives in one place."""

from typing import Any

from rest_framework import serializers

from apps.assessments.models import Assessment
from apps.common.errors import ERROR_CODES


class DefectClassSerializer(serializers.Serializer):
    key = serializers.CharField()
    name = serializers.CharField()
    category = serializers.ChoiceField(choices=["primary", "secondary"])


class BoundingBoxSerializer(serializers.Serializer):
    x1 = serializers.FloatField()
    y1 = serializers.FloatField()
    x2 = serializers.FloatField()
    y2 = serializers.FloatField()


class DetectionSerializer(serializers.Serializer):
    defect = DefectClassSerializer()
    confidence = serializers.FloatField(help_text="Model confidence; not the probability it is correct.")
    box = BoundingBoxSerializer()


class ClassTallySerializer(serializers.Serializer):
    defect = DefectClassSerializer()
    count = serializers.IntegerField()
    mean_confidence = serializers.FloatField()


class SummarySerializer(serializers.Serializer):
    detection_count = serializers.IntegerField(help_text="All defect detections. Not a bean count.")
    primary_detection_count = serializers.IntegerField()
    secondary_detection_count = serializers.IntegerField()
    by_class = ClassTallySerializer(many=True)


class CoverageSerializer(serializers.Serializer):
    scanned = DefectClassSerializer(many=True)
    not_scanned = DefectClassSerializer(many=True)


class LimitationSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()


class BilingualSerializer(serializers.Serializer):
    en = serializers.CharField()
    am = serializers.CharField(help_text="Amharic")


class AdvisorySerializer(serializers.Serializer):
    generator_model = serializers.CharField()
    summary = BilingualSerializer()
    recommendations = BilingualSerializer(many=True)


class ImagesSerializer(serializers.Serializer):
    original_url = serializers.CharField(allow_null=True)
    annotated_url = serializers.CharField(allow_null=True)
    expires_in_s = serializers.IntegerField()


class ImageCheckSerializer(serializers.Serializer):
    is_coffee = serializers.BooleanField(help_text="Always true here; non-coffee photos are rejected.")
    coffee_confidence = serializers.FloatField()
    validator_version = serializers.CharField()


class ResultSerializer(serializers.Serializer):
    model_version = serializers.CharField()
    image_check = ImageCheckSerializer()
    summary = SummarySerializer()
    detections = DetectionSerializer(many=True)
    coverage = CoverageSerializer()
    limitations = LimitationSerializer(many=True)
    advisory = AdvisorySerializer()
    images = ImagesSerializer()


class CompletedAssessmentSerializer(serializers.Serializer):
    assessment_id = serializers.CharField()
    status = serializers.ChoiceField(choices=["completed"])
    created_at = serializers.DateTimeField()
    processing_time_ms = serializers.IntegerField()
    result = ResultSerializer()


class FailedAssessmentSerializer(serializers.Serializer):
    assessment_id = serializers.CharField()
    status = serializers.ChoiceField(choices=["failed"])
    created_at = serializers.DateTimeField()
    processing_time_ms = serializers.IntegerField()
    error_code = serializers.CharField()


class CompletedListItemSerializer(serializers.Serializer):
    assessment_id = serializers.CharField()
    status = serializers.ChoiceField(choices=["completed"])
    created_at = serializers.DateTimeField()
    model_version = serializers.CharField()
    detection_count = serializers.IntegerField()
    primary_detection_count = serializers.IntegerField()
    secondary_detection_count = serializers.IntegerField()


class FailedListItemSerializer(serializers.Serializer):
    assessment_id = serializers.CharField()
    status = serializers.ChoiceField(choices=["failed"])
    created_at = serializers.DateTimeField()
    error_code = serializers.CharField()


def render_assessment(data: dict[str, Any]) -> Any:
    serializer = CompletedAssessmentSerializer if data["status"] == "completed" else FailedAssessmentSerializer
    return serializer(data).data


def render_list_item(data: dict[str, Any]) -> Any:
    serializer = CompletedListItemSerializer if data["status"] == "completed" else FailedListItemSerializer
    return serializer(data).data


# --- admin ---------------------------------------------------------------------------------


class AdminAssessmentSerializer(serializers.ModelSerializer):
    assessment_id = serializers.CharField(source="id")
    owner_id = serializers.UUIDField(read_only=True)
    detection_count = serializers.SerializerMethodField(help_text="Set when completed.")

    class Meta:
        model = Assessment
        fields = [
            "assessment_id", "owner_id", "status", "created_at", "processing_time_ms",
            "error_code", "model_version", "validator_version", "detection_count",
        ]

    def get_detection_count(self, obj: Assessment) -> int | None:
        return None if obj.result is None else len(obj.result["detections"])


class AdminFilterSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Assessment.Status.choices, required=False)
    error_code = serializers.ChoiceField(choices=ERROR_CODES, required=False)
    owner_id = serializers.UUIDField(required=False)


class ModelVersionUsageSerializer(serializers.Serializer):
    model_version = serializers.CharField()
    validator_version = serializers.CharField()
    assessments = serializers.IntegerField()
    first_seen = serializers.DateTimeField()
    last_seen = serializers.DateTimeField()


class ModelVersionsSerializer(serializers.Serializer):
    versions = ModelVersionUsageSerializer(many=True)


class OutcomeSerializer(serializers.Serializer):
    status = serializers.CharField()
    error_code = serializers.CharField(allow_null=True)
    count = serializers.IntegerField()


class OverviewQuerySerializer(serializers.Serializer):
    window_hours = serializers.IntegerField(min_value=1, max_value=720, default=24)


class OverviewSerializer(serializers.Serializer):
    since = serializers.DateTimeField()
    window_hours = serializers.IntegerField()
    outcomes = OutcomeSerializer(many=True)


class LimitsSerializer(serializers.Serializer):
    max_image_bytes = serializers.IntegerField()
    max_image_pixels = serializers.IntegerField()
    min_image_side_px = serializers.IntegerField()
    max_assessments_per_user_per_hour = serializers.IntegerField()
    max_concurrent_assessments = serializers.IntegerField(help_text="gunicorn workers x threads")
    vision_timeout_s = serializers.FloatField()
    gemini_timeout_s = serializers.FloatField()
    image_url_ttl_s = serializers.IntegerField()
    retain_original_image = serializers.BooleanField()


class ModelReloadSerializer(serializers.Serializer):
    reloaded = serializers.BooleanField()
    engine = serializers.CharField()
