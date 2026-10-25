from django.contrib import admin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Accounts are created through the API or `createsuperuser`; here an admin can deactivate a
    user or tick `is_staff` to make an administrator. Passwords cannot be viewed or edited."""

    list_display = ("email", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_active")
    search_fields = ("email",)
    ordering = ("-date_joined",)
    fields = ("email", "is_active", "is_staff", "is_superuser", "date_joined", "last_login")
    readonly_fields = ("email", "date_joined", "last_login")

    def has_add_permission(self, request):  # noqa: ANN001, ANN201
        return False

    def has_delete_permission(self, request, obj=None):  # noqa: ANN001, ANN201
        return False
