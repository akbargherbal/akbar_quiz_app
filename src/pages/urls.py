# src/pages/urls.py

from django.urls import path
from . import views

app_name = "pages"  # Namespace for these URLs

urlpatterns = [
    # Public-facing pages
    path("", views.home, name="home"),  # Homepage
    path("quizzes/", views.quizzes, name="quizzes"),  # Quiz browsing page
    path("about/", views.about, name="about"),  # About page
    # Placeholder/User-related pages (Login URL is removed)
    path("signup/", views.signup_view, name="signup"),  # Placeholder signup
    path(
        "profile/", views.profile_view, name="profile"
    ),  # User profile page (requires login)
    # Removed the placeholder login path:
    # path("login/", views.login_view, name="login"), # <<< THIS LINE IS DELETED
]

# Notes:
# - The path for '/login/' served by pages.views.login_view is removed.
# - URLs like {% url 'pages:login' %} will no longer work.
# - To link to the login page, you should now use {% url 'login' %} which will
#   resolve to '/accounts/login/' based on the core urls.py configuration.
