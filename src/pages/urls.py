# src/pages/urls.py

from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [
    path("", views.home, name="home"),
    path("quizzes/", views.quizzes, name="quizzes"),
    path("about/", views.about, name="about"),
    path("signup/", views.signup_view, name="signup"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile_view, name="edit_profile"),  # <<< NEW URL
]
