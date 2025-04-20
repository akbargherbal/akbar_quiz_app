from django.contrib import admin
from django.urls import path, include
from multi_choice_quiz import views as multi_choice_quiz_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("quiz/", include("multi_choice_quiz.urls")),
    path("", include("pages.urls")),  # Notice: no 'name' parameter here
    path("", include("pwa.urls")),
]
