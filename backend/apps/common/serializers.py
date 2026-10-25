"""Schema-only serializers for the error envelope, and the helper routers use to document it."""

from rest_framework import serializers

from apps.common.errors import ERROR_CODES


class ErrorBodySerializer(serializers.Serializer):
    code = serializers.ChoiceField(choices=ERROR_CODES)
    message = serializers.CharField(help_text="Safe to show to a user.")
    request_id = serializers.CharField(help_text="Quote this when reporting a problem.")
    assessment_id = serializers.CharField(allow_null=True)
    details = serializers.DictField(allow_null=True, help_text="For IMAGE_NOT_COFFEE: is_coffee, coffee_confidence, threshold.")


class ErrorResponseSerializer(serializers.Serializer):
    error = ErrorBodySerializer()


def errors(*statuses: int) -> dict[int, type[ErrorResponseSerializer]]:
    return dict.fromkeys(statuses, ErrorResponseSerializer)
