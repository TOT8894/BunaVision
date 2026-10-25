from django.urls import path

from apps.accounts import views

urlpatterns = [
    path("register", views.RegisterView.as_view()),
    path("login", views.LoginView.as_view()),
    path("me", views.MeView.as_view()),
]
