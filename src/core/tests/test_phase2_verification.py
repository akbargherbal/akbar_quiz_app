# src/pages/tests/test_phase2_verification.py

import pytest
from pathlib import Path
import importlib

from django.conf import settings
from django.urls import reverse, NoReverseMatch
from django.contrib.auth.forms import UserCreationForm
from django.test import Client

# Try importing the specific form
try:
    from pages.forms import SignUpForm

    SIGNUP_FORM_EXISTS = True
except ImportError:
    SignUpForm = None  # Set to None if import fails
    SIGNUP_FORM_EXISTS = False

# Mark all tests in this module as needing database access for Client and potentially form checks
pytestmark = pytest.mark.django_db

# --- Constants ---
EXPECTED_SIGNUP_URL_PATH = "/signup/"
SIGNUP_TEMPLATE_NAME = "pages/signup.html"
SIGNUP_FORM_MODULE_PATH = "pages.forms"
SIGNUP_VIEW_MODULE_PATH = "pages.views"
BASE_TEMPLATE_MARKER = "<header"  # A simple marker from pages/base.html
BASE_TEMPLATE_NAME = "pages/base.html"


class TestPhase2Verification:
    """
    Verifies the successful completion of Phase 2: User Registration (Signup).
    Focuses on the correct setup of forms, views, URLs, and templates.
    """

    # --- Step 2.1: Create Signup Form & View ---

    def test_signup_form_module_exists(self):
        """Verify that the 'pages/forms.py' module can be imported."""
        try:
            importlib.import_module(SIGNUP_FORM_MODULE_PATH)
        except ImportError:
            pytest.fail(
                f"Could not import the module '{SIGNUP_FORM_MODULE_PATH}'. Does 'pages/forms.py' exist?"
            )

    def test_signup_form_class_exists_and_inherits(self):
        """Verify SignUpForm exists in pages.forms and inherits from UserCreationForm."""
        assert (
            SIGNUP_FORM_EXISTS
        ), f"Could not import 'SignUpForm' from '{SIGNUP_FORM_MODULE_PATH}'. Does the class exist?"
        assert issubclass(
            SignUpForm, UserCreationForm
        ), f"'SignUpForm' in '{SIGNUP_FORM_MODULE_PATH}' must inherit from 'django.contrib.auth.forms.UserCreationForm'."

    def test_signup_view_exists(self):
        """Verify that 'signup_view' exists in the pages.views module."""
        try:
            views_module = importlib.import_module(SIGNUP_VIEW_MODULE_PATH)
        except ImportError:
            pytest.fail(
                f"Could not import the module '{SIGNUP_VIEW_MODULE_PATH}'. Does 'pages/views.py' exist?"
            )
        assert hasattr(
            views_module, "signup_view"
        ), f"Could not find a function or class named 'signup_view' in '{SIGNUP_VIEW_MODULE_PATH}'."

    def test_signup_url_resolves(self):
        """Verify the '/signup/' URL resolves to the 'pages:signup' name."""
        try:
            signup_url = reverse("pages:signup")
            assert (
                signup_url == EXPECTED_SIGNUP_URL_PATH
            ), f"reverse('pages:signup') resolved to '{signup_url}', expected '{EXPECTED_SIGNUP_URL_PATH}'"
        except NoReverseMatch:
            pytest.fail(
                "URL pattern named 'pages:signup' could not be reversed. Check pages/urls.py."
            )

    # --- Step 2.2: Implement Signup Template ---

    def test_signup_template_exists(self):
        """Verify 'pages/templates/pages/signup.html' exists."""
        template_path = settings.BASE_DIR / "pages" / "templates" / SIGNUP_TEMPLATE_NAME
        assert (
            template_path.exists()
        ), f"Signup template file not found at '{template_path}'"

    def test_signup_view_get_request_renders_form(self, client: Client):
        """Verify GET request to /signup/ returns 200 and contains the form."""
        try:
            signup_url = reverse("pages:signup")
        except NoReverseMatch:
            pytest.fail(
                "Cannot test signup view rendering because 'pages:signup' URL did not resolve."
            )

        response = client.get(signup_url)
        assert (
            response.status_code == 200
        ), f"GET request to {signup_url} failed with status {response.status_code}"

        # Check if the context contains a form
        assert (
            "form" in response.context
        ), "The context dictionary for the signup view is missing the 'form' key."
        assert (
            response.context["form"] is not None
        ), "The 'form' in the signup view context is None."

        # Check if the form in context is the correct type
        if SIGNUP_FORM_EXISTS:
            assert isinstance(
                response.context["form"], SignUpForm
            ), f"The 'form' in context is not an instance of SignUpForm (it's type: {type(response.context['form'])})."
        else:
            # Fallback check if SignUpForm couldn't be imported
            assert isinstance(
                response.context["form"], UserCreationForm
            ), f"The 'form' in context is not an instance of UserCreationForm (it's type: {type(response.context['form'])})."

    def test_signup_template_renders_correctly(self, client: Client):
        """Verify the rendered signup template has essential form elements and extends base."""
        try:
            signup_url = reverse("pages:signup")
        except NoReverseMatch:
            pytest.fail(
                "Cannot test signup template rendering because 'pages:signup' URL did not resolve."
            )

        response = client.get(signup_url)
        assert response.status_code == 200

        response_content = response.content.decode("utf-8")

        # 1. Check base template extension
        assert (
            BASE_TEMPLATE_MARKER in response_content
        ), f"Signup template does not seem to extend '{BASE_TEMPLATE_NAME}' (missing marker: '{BASE_TEMPLATE_MARKER}')"

        # 2. Check for CSRF token
        assert (
            'name="csrfmiddlewaretoken"' in response_content
        ), "CSRF token hidden input ('csrfmiddlewaretoken') not found in the rendered signup form."

        # 3. Check for form method
        assert (
            'method="POST"' in response_content or 'method="post"' in response_content
        ), "Signup form does not have method='POST'."

        # 4. Check for common UserCreationForm fields (presence suggests {{ form.as_p }} or similar was used)
        #    These names are standard for UserCreationForm
        assert (
            'name="username"' in response_content
        ), "Input field with name='username' not found in the signup form."
        # --- START CORRECTION ---
        assert (
            'name="password1"' in response_content
        ), "Input field with name='password1' not found in the signup form (this is the standard UserCreationForm field)."
        # --- END CORRECTION ---
        assert (
            'name="password2"' in response_content
        ), "Input field with name='password2' (password confirmation) not found in the signup form."
