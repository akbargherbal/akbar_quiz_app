"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from multi_choice_quiz import views as multi_choice_quiz_views


# Add this near the top of the file with the other imports
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


# Add this inside the file
@csrf_exempt
def test_debug_view(request):
    """A diagnostic view to troubleshoot deployment issues."""
    import os
    import sys
    import json
    from django.conf import settings

    # Get environment data
    env_data = dict(os.environ)
    # Mask sensitive information
    for key in ["SECRET_KEY", "DB_PASSWORD"]:
        if key in env_data:
            env_data[key] = "[REDACTED]"

    # Get database settings
    db_info = settings.DATABASES["default"].copy()
    if "PASSWORD" in db_info:
        db_info["PASSWORD"] = "[REDACTED]"

    # Test database connectivity
    db_working = False
    db_error = None
    try:
        from django.db import connection

        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        db_working = cursor.fetchone()[0] == 1
    except Exception as e:
        db_error = str(e)

    # Build response
    data = {
        "environment": os.environ.get("ENVIRONMENT"),
        "is_appengine": os.environ.get("GAE_APPLICATION") is not None,
        "database_engine": db_info.get("ENGINE"),
        "database_working": db_working,
        "database_error": db_error,
        "allowed_hosts": settings.ALLOWED_HOSTS,
        "debug_mode": settings.DEBUG,
    }

    return HttpResponse(
        f"<pre>{json.dumps(data, indent=2)}</pre>", content_type="text/html"
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("quiz/", include("multi_choice_quiz.urls")),
    path("", include("pages.urls")),  # Notice: no 'name' parameter here
    path("", include("pwa.urls")),
    path("debug-info/", test_debug_view, name="debug_info"),
]
