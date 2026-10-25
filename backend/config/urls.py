from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def health(request):  # noqa: ANN001, ANN201
    """Liveness only: exposes no configuration."""
    return JsonResponse({"status": "ok", "version": settings.APP_VERSION})


urlpatterns = [
    path("health", health),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.assessments.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("django-admin/", admin.site.urls),
]
