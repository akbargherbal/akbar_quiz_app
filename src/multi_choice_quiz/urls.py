from django.urls import path
from . import views

app_name = "multi_choice_quiz"

urlpatterns = [
    path("", views.home, name="home"),
    # Add other URL patterns as needed
]
