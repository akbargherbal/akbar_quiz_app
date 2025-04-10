# src/multi_choice_quiz/urls.py

from django.urls import path
from . import views

app_name = "multi_choice_quiz"

urlpatterns = [
    path("", views.home, name="home"),
    path("<int:quiz_id>/", views.quiz_detail, name="quiz_detail"),
    # Add other URL patterns as needed
]
