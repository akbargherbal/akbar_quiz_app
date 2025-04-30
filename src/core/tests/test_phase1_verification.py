# src/core/tests/test_phase1_verification.py
# REVISED to use Django's TestCase client

import logging

# import pytest # No longer strictly needed for markers here
from django.conf import settings
from django.urls import resolve, Resolver404
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.views import LoginView, LogoutView

# Import Django's TestCase
from django.test import Client, TestCase  # <<< CHANGE HERE: Import TestCase
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger("phase1_verification")


# Inherit from TestCase instead of object
class TestPhase1Verification(TestCase):  # <<< CHANGE HERE
    """Tests specifically verifying the configuration and setup after Phase 1."""

    # No need for @pytest.mark.django_db when inheriting from TestCase

    def test_auth_apps_configured(self):
        """Verify that required authentication apps are in INSTALLED_APPS."""
        logger.info("Verifying Step 1.1: Auth apps in INSTALLED_APPS...")
        installed_apps = settings.INSTALLED_APPS
        self.assertIn(
            "django.contrib.auth",
            installed_apps,
            "'django.contrib.auth' not found in INSTALLED_APPS",
        )
        self.assertIn(
            "django.contrib.sessions",
            installed_apps,
            "'django.contrib.sessions' not found in INSTALLED_APPS",
        )
        logger.info(
            "SUCCESS: 'django.contrib.auth' and 'django.contrib.sessions' are in INSTALLED_APPS."
        )

    def test_auth_middleware_configured(self):
        """Verify that required authentication middleware is in MIDDLEWARE and ordered correctly."""
        logger.info("Verifying Step 1.1: Auth middleware in MIDDLEWARE...")
        middleware = settings.MIDDLEWARE
        session_middleware_fqn = "django.contrib.sessions.middleware.SessionMiddleware"
        auth_middleware_fqn = "django.contrib.auth.middleware.AuthenticationMiddleware"

        self.assertIn(
            session_middleware_fqn,
            middleware,
            f"'{session_middleware_fqn}' not found in MIDDLEWARE",
        )
        self.assertIn(
            auth_middleware_fqn,
            middleware,
            f"'{auth_middleware_fqn}' not found in MIDDLEWARE",
        )

        try:
            session_index = middleware.index(session_middleware_fqn)
            auth_index = middleware.index(auth_middleware_fqn)
            self.assertLess(
                session_index,
                auth_index,
                f"'{session_middleware_fqn}' must come before '{auth_middleware_fqn}' in MIDDLEWARE",
            )
            logger.info(
                f"SUCCESS: '{session_middleware_fqn}' found at index {session_index}."
            )
            logger.info(
                f"SUCCESS: '{auth_middleware_fqn}' found at index {auth_index}."
            )
            logger.info("SUCCESS: Middleware order is correct.")
        except ValueError:
            self.fail(
                "One or both required middleware classes not found."
            )  # Use self.fail

    def test_auth_urls_resolve(self):
        """Verify that standard auth URLs resolve to the correct views."""
        logger.info("Verifying Step 1.2: Default auth URLs resolve...")
        try:
            login_match = resolve("/accounts/login/")
            self.assertEqual(
                login_match.func.view_class,
                LoginView,
                f"URL /accounts/login/ resolved to {login_match.func}, expected LoginView",
            )
            logger.info("SUCCESS: '/accounts/login/' resolves to LoginView.")

            logout_match = resolve("/accounts/logout/")
            self.assertEqual(
                logout_match.func.view_class,
                LogoutView,
                f"URL /accounts/logout/ resolved to {logout_match.func}, expected LogoutView",
            )
            logger.info("SUCCESS: '/accounts/logout/' resolves to LogoutView.")

        except Resolver404 as e:
            self.fail(f"Could not resolve standard auth URL: {e}")  # Use self.fail

    def test_auth_models_available(self):
        """Verify that core auth models are available and queryable."""
        logger.info("Verifying Step 1.3: Core auth models are available...")
        try:
            logger.info("SUCCESS: Imported User, Group, Permission models.")
            # Database check: Can we perform a basic query?
            self.assertFalse(User.objects.exists())  # Use standard unittest assert
            self.assertFalse(Group.objects.exists())
            self.assertTrue(Permission.objects.exists())  # Use standard unittest assert
            logger.info(
                "SUCCESS: Basic queries on User, Group, Permission models successful (confirms tables exist in test DB)."
            )
        except Exception as e:
            self.fail(
                f"Error accessing auth models or querying database: {e}"
            )  # Use self.fail

    # Remove client fixture parameter, use self.client instead
    def test_request_user_attribute_exists(self):  # <<< CHANGE HERE
        """Verify that the 'user' attribute is added to requests."""
        logger.info("Verifying Middleware: 'user' attribute exists on request...")
        try:
            # Use self.client provided by TestCase
            response = self.client.get("/")  # <<< CHANGE HERE
            self.assertEqual(
                response.status_code,
                200,
                f"Homepage request failed with status {response.status_code}",
            )

            # Check if the user attribute exists on the WSGIRequest attached to the response
            self.assertTrue(
                hasattr(response.wsgi_request, "user"),
                "'user' attribute not found on request object.",
            )
            logger.info("SUCCESS: 'user' attribute found on request.")

            # Check if the default user is AnonymousUser
            self.assertIsInstance(
                response.wsgi_request.user,
                AnonymousUser,
                f"Expected AnonymousUser, but got {type(response.wsgi_request.user)}",
            )
            logger.info(
                f"SUCCESS: Request user is of type '{type(response.wsgi_request.user).__name__}'."
            )

        except Exception as e:
            self.fail(
                f"Error during request or checking 'user' attribute: {e}"
            )  # Use self.fail
