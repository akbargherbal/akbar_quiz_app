# src/core/urls.py

from django.contrib import admin
from django.urls import path, include

# No need to import auth_views if using the standard include below

urlpatterns = [
    # Django Admin Interface
    path("admin/", admin.site.urls),
    # Your Applications
    path("quiz/", include("multi_choice_quiz.urls")),  # Quiz app URLs
    path("", include("pages.urls")),  # Pages app URLs (handles root path '/')
    path("", include("pwa.urls")),  # PWA app URLs (also at root)
    # Django's Built-in Authentication URLs
    # This includes paths like:
    # accounts/login/
    # accounts/logout/
    # accounts/password_change/
    # accounts/password_change/done/
    # accounts/password_reset/
    # accounts/password_reset/done/
    # accounts/reset/<uidb64>/<token>/
    # accounts/reset/done/
    # It uses the URL names like 'login', 'logout', 'password_reset', etc.
    path("accounts/", include("django.contrib.auth.urls")),
]

# Notes:
# - We removed the specific override for LoginView.
# - Make sure settings.LOGIN_URL = 'login'.
# - Make sure the login template is now located at 'templates/registration/login.html'
#   and settings.TEMPLATES['DIRS'] points to the top-level 'templates' directory.
