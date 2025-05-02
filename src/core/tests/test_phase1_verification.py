# src/core/tests/test_phase1_verification.py

import pytest
from pathlib import Path
from django.conf import settings
from django.urls import reverse, NoReverseMatch
from django.template.loader import get_template, TemplateDoesNotExist
from django.test import Client
from django.contrib.auth import get_user_model

# Mark all tests in this module as needing database access (even if just for settings/client)
pytestmark = pytest.mark.django_db

# --- Constants ---
EXPECTED_LOGIN_URL_PATH = "/accounts/login/"
EXPECTED_LOGOUT_URL_PATH = "/accounts/logout/"
LOGIN_TEMPLATE_NAME = "registration/login.html"
LOGGED_OUT_TEMPLATE_NAME = "registration/logged_out.html"
BASE_TEMPLATE_MARKER = "<header"  # A simple marker from pages/base.html
BASE_TEMPLATE_NAME = "pages/base.html"  # For checking template extension


class TestPhase1Verification:
    """
    Verifies the successful completion of Phase 1:
    Enable Core Django Auth Backend & Basic Templates.
    """

    # --- Step 1.1: Configure Auth Apps & Middleware ---

    def test_auth_apps_configured(self):
        """Verify 'django.contrib.auth' and 'django.contrib.sessions' are in INSTALLED_APPS."""
        assert (
            "django.contrib.auth" in settings.INSTALLED_APPS
        ), "'django.contrib.auth' not found in INSTALLED_APPS"
        assert (
            "django.contrib.sessions" in settings.INSTALLED_APPS
        ), "'django.contrib.sessions' not found in INSTALLED_APPS"

    def test_auth_middleware_configured(self):
        """Verify SessionMiddleware and AuthenticationMiddleware are in MIDDLEWARE."""
        assert (
            "django.contrib.sessions.middleware.SessionMiddleware"
            in settings.MIDDLEWARE
        ), "'SessionMiddleware' not found in MIDDLEWARE"
        assert (
            "django.contrib.auth.middleware.AuthenticationMiddleware"
            in settings.MIDDLEWARE
        ), "'AuthenticationMiddleware' not found in MIDDLEWARE"
        # Optional: Check order (SessionMiddleware should ideally be before AuthenticationMiddleware)
        try:
            session_index = settings.MIDDLEWARE.index(
                "django.contrib.sessions.middleware.SessionMiddleware"
            )
            auth_index = settings.MIDDLEWARE.index(
                "django.contrib.auth.middleware.AuthenticationMiddleware"
            )
            assert (
                session_index < auth_index
            ), "SessionMiddleware should come before AuthenticationMiddleware in MIDDLEWARE"
        except ValueError:
            # This case is already covered by the individual asserts above
            pass

    # --- Step 1.2: Include Default Auth URLs ---

    def test_login_logout_settings_configured(self):
        """Verify LOGIN_URL, LOGIN_REDIRECT_URL, and LOGOUT_REDIRECT_URL are set."""
        assert (
            settings.LOGIN_URL == "login"
        ), f"settings.LOGIN_URL should be 'login', but found '{settings.LOGIN_URL}'"
        assert hasattr(
            settings, "LOGIN_REDIRECT_URL"
        ), "settings.LOGIN_REDIRECT_URL is not defined"
        assert (
            settings.LOGIN_REDIRECT_URL
        ), "settings.LOGIN_REDIRECT_URL should not be empty"  # Check it's not empty
        assert hasattr(
            settings, "LOGOUT_REDIRECT_URL"
        ), "settings.LOGOUT_REDIRECT_URL is not defined"
        assert (
            settings.LOGOUT_REDIRECT_URL
        ), "settings.LOGOUT_REDIRECT_URL should not be empty"  # Check it's not empty

    def test_auth_urls_included_and_resolvable(self):
        """Verify standard auth URLs are included and resolve correctly."""
        try:
            login_url = reverse("login")
            assert (
                login_url == EXPECTED_LOGIN_URL_PATH
            ), f"reverse('login') resolved to '{login_url}', expected '{EXPECTED_LOGIN_URL_PATH}'"
        except NoReverseMatch:
            pytest.fail(
                "URL pattern named 'login' could not be reversed. Check core/urls.py and include('django.contrib.auth.urls')."
            )

        try:
            logout_url = reverse("logout")
            assert (
                logout_url == EXPECTED_LOGOUT_URL_PATH
            ), f"reverse('logout') resolved to '{logout_url}', expected '{EXPECTED_LOGOUT_URL_PATH}'"
        except NoReverseMatch:
            pytest.fail(
                "URL pattern named 'logout' could not be reversed. Check core/urls.py and include('django.contrib.auth.urls')."
            )

        # Check a few other standard auth URLs are present
        try:
            reverse("password_reset")
        except NoReverseMatch:
            pytest.fail("URL pattern named 'password_reset' could not be reversed.")
        try:
            reverse("password_change")
        except NoReverseMatch:
            pytest.fail("URL pattern named 'password_change' could not be reversed.")

    # --- Step 1.3: Apply Auth Migrations ---

    def test_user_model_available(self):
        """Verify the standard User model can be imported (proxy for migrations applied)."""
        try:
            UserModel = get_user_model()
            assert UserModel is not None, "get_user_model() returned None"
            # Optional: Check if the model has expected fields like 'username'
            assert hasattr(
                UserModel, "username"
            ), "User model does not have a 'username' attribute"
        except Exception as e:
            pytest.fail(
                f"Could not get User model. Migrations likely missing or failed. Error: {e}"
            )

    # --- Step 1.4: Create/Customize Core Auth Templates ---

    def test_templates_dir_configured(self):
        """Verify the top-level 'templates' directory is in settings.TEMPLATES DIRS."""
        expected_templates_dir = settings.BASE_DIR / "templates"
        configured_dirs = settings.TEMPLATES[0].get("DIRS", [])
        assert any(
            Path(d) == expected_templates_dir for d in configured_dirs
        ), f"Top-level templates directory '{expected_templates_dir}' not found in settings.TEMPLATES[0]['DIRS']"

    def test_login_template_exists_and_loads(self):
        """Verify 'templates/registration/login.html' exists and can be loaded."""
        template_path = settings.BASE_DIR / "templates" / LOGIN_TEMPLATE_NAME
        assert (
            template_path.exists()
        ), f"Login template file not found at '{template_path}'"
        try:
            get_template(LOGIN_TEMPLATE_NAME)
        except TemplateDoesNotExist:
            pytest.fail(
                f"Django could not load the template '{LOGIN_TEMPLATE_NAME}'. Check TEMPLATES settings and file location."
            )

    def test_logged_out_template_exists_and_loads(self):
        """Verify 'templates/registration/logged_out.html' exists and can be loaded."""
        template_path = settings.BASE_DIR / "templates" / LOGGED_OUT_TEMPLATE_NAME
        assert (
            template_path.exists()
        ), f"Logged out template file not found at '{template_path}'"
        try:
            get_template(LOGGED_OUT_TEMPLATE_NAME)
        except TemplateDoesNotExist:
            pytest.fail(
                f"Django could not load the template '{LOGGED_OUT_TEMPLATE_NAME}'. Check TEMPLATES settings and file location."
            )

    def test_login_view_renders_styled_template(self, client: Client):
        """Verify the login page loads, uses the base template, and has required elements."""
        try:
            login_url = reverse("login")
        except NoReverseMatch:
            pytest.fail(
                "Cannot test login view rendering because 'login' URL did not resolve."
            )

        response = client.get(login_url)

        assert (
            response.status_code == 200
        ), f"GET request to {login_url} failed with status {response.status_code}"

        # 1. Check if it extends the base template (look for a unique element/string)
        response_content = response.content.decode("utf-8")
        assert (
            BASE_TEMPLATE_MARKER in response_content
        ), f"Login template does not seem to extend '{BASE_TEMPLATE_NAME}' (missing marker: '{BASE_TEMPLATE_MARKER}')"

        # 2. Check for CSRF token
        assert (
            "{% csrf_token %}" not in response_content
        ), "Template seems to contain the literal '{% csrf_token %}' tag instead of the rendered input."
        assert (
            'name="csrfmiddlewaretoken"' in response_content
        ), "CSRF token hidden input ('csrfmiddlewaretoken') not found in the rendered login form."

        # 3. Check for form elements
        assert (
            'name="username"' in response_content
        ), "Input field with name='username' not found in the login form."
        assert (
            'name="password"' in response_content
        ), "Input field with name='password' not found in the login form."
        assert (
            'method="POST"' in response_content or 'method="post"' in response_content
        ), "Login form does not have method='POST'."

    # --- Step 1.5: Full Regression Test (Minimal Smoke Test) ---
    # Note: Full regression is handled by running *all* tests, but we add a basic check.

    def test_homepage_loads_after_auth_setup(self, client: Client):
        """Basic smoke test to ensure the homepage still loads after Phase 1 changes."""
        try:
            home_url = reverse("pages:home")  # Assumes 'pages' app handles homepage
        except NoReverseMatch:
            pytest.fail(
                "Cannot run homepage smoke test because 'pages:home' URL did not resolve."
            )

        response = client.get(home_url)
        assert (
            response.status_code == 200
        ), f"Homepage ({home_url}) failed to load (status {response.status_code}) after Phase 1 setup."
