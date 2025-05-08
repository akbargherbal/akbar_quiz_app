# src/multi_choice_quiz/urls.py

from django.urls import path
from . import views

app_name = "multi_choice_quiz"

urlpatterns = [
    path("", views.home, name="home"),
    path("<int:quiz_id>/", views.quiz_detail, name="quiz_detail"),
    path("submit_attempt/", views.submit_quiz_attempt, name="submit_quiz_attempt"),
    # <<< START NEW URL PATTERN (Step 7.1) >>>
    path(
        "attempt/<int:attempt_id>/review/",
        views.attempt_mistake_review,
        name="attempt_mistake_review",
    ),
    # <<< END NEW URL PATTERN >>>
]
