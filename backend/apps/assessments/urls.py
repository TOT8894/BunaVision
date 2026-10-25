from django.urls import path

from apps.assessments import admin_views, views

urlpatterns = [
    path("assessments", views.AssessmentListCreateView.as_view()),
    path("assessments/<str:assessment_id>", views.AssessmentDetailView.as_view()),
    path("admin/assessments", admin_views.AdminAssessmentListView.as_view()),
    path("admin/assessments/<str:assessment_id>", admin_views.AdminAssessmentDetailView.as_view()),
    path("admin/model-versions", admin_views.AdminModelVersionsView.as_view()),
    path("admin/overview", admin_views.AdminOverviewView.as_view()),
    path("admin/limits", admin_views.AdminLimitsView.as_view()),
    path("admin/vision/reload-model", admin_views.AdminReloadModelView.as_view()),
]
