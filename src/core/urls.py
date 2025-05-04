# src/core/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings  # <-- Import settings
from django.conf.urls.static import static  # If you need static/media in DEBUG

# No need to import auth_views if using the standard include below

urlpatterns = [
    # Django Admin Interface
    path("admin/", admin.site.urls),

    # Your Applications
    path("quiz/", include("multi_choice_quiz.urls")),  # Quiz app URLs
    path("", include("pages.urls")),  # Pages app URLs (handles root path '/')
    path("", include("pwa.urls")),  # PWA app URLs (also at root)

    # Django's Built-in Authentication URLs (Keep the simple include)
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


# --- Add this block for Django Debug Toolbar ---
if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

    # Optional: Serve static/media files locally during development
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # If you use media files
# -----------------------------------------------