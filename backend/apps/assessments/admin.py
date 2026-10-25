from django.contrib import admin

from apps.assessments.models import Assessment


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    """Read-only dashboard for "processing failures recorded" and "model versions recorded"."""

    list_display = ("id", "owner", "status", "error_code", "model_version", "validator_version", "created_at", "processing_time_ms")
    list_filter = ("status", "error_code", "model_version", "validator_version")
    search_fields = ("id", "owner__email")
    list_select_related = ("owner",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):  # noqa: ANN001, ANN201
        return False

    def has_change_permission(self, request, obj=None):  # noqa: ANN001, ANN201
        return False

    def has_delete_permission(self, request, obj=None):  # noqa: ANN001, ANN201
        return False
