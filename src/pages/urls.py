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
    path("profile/edit/", views.edit_profile_view, name="edit_profile"),
    path(
        "profile/collections/create/",
        views.create_collection_view,
        name="create_collection",
    ),
    path(
        "profile/collections/<int:collection_id>/remove_quiz/<int:quiz_id>/",
        views.remove_quiz_from_collection_view,
        name="remove_quiz_from_collection",
    ),
    path(
        "quiz/<int:quiz_id>/add-to-collection/",
        views.select_collection_for_quiz_view,
        name="select_collection_for_quiz",
    ),
    # --- NEW URL PATTERN for adding a quiz to a specific collection ---
    path(
        "quiz/<int:quiz_id>/add-to-collection/<int:collection_id>/",
        views.add_quiz_to_selected_collection_view,  # We will create this view next
        name="add_quiz_to_selected_collection",
    ),
]
