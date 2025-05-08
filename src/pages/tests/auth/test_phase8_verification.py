# Pages app tests package
# src/pages/tests/auth/test_phase8_verification.py

from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import (
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth import get_user_model

# Import the standardized logging setup
from multi_choice_quiz.tests.test_logging import setup_test_logging

logger = setup_test_logging(__name__, "pages_auth")  # Log under pages app

User = get_user_model()


class Phase8PasswordMgmtVerificationTests(TestCase):
    """
    Verify the integration and basic rendering of Django's password
    management views using our custom templates (Phase 8).
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="pwdtester", password="password123"
        )
        # URLs to test
        cls.password_change_url = reverse("password_change")
        cls.password_change_done_url = reverse("password_change_done")
        cls.password_reset_url = reverse("password_reset")
        cls.password_reset_done_url = reverse("password_reset_done")
        # Need dummy args for confirm/complete, resolve() doesn't need them
        cls.password_reset_confirm_name = "password_reset_confirm"
        cls.password_reset_complete_url = reverse("password_reset_complete")

    def test_password_mgmt_urls_resolve_correctly(self):
        """Verify URLs resolve to the correct Django auth views."""
        logger.info("Verifying password management URL resolution...")
        self.assertEqual(
            resolve(self.password_change_url).func.view_class,
            auth_views.PasswordChangeView,
        )
        self.assertEqual(
            resolve(self.password_change_done_url).func.view_class,
            auth_views.PasswordChangeDoneView,
        )
        self.assertEqual(
            resolve(self.password_reset_url).func.view_class,
            auth_views.PasswordResetView,
        )
        self.assertEqual(
            resolve(self.password_reset_done_url).func.view_class,
            auth_views.PasswordResetDoneView,
        )
        # Confirm resolve needs uidb64 and token args - just check view name matches
        self.assertEqual(
            resolve(
                reverse(self.password_reset_confirm_name, args=["uidb64", "token"])
            ).func.view_class,
            auth_views.PasswordResetConfirmView,
        )
        self.assertEqual(
            resolve(self.password_reset_complete_url).func.view_class,
            auth_views.PasswordResetCompleteView,
        )
        logger.info("Password management URL resolution verified.")

    def test_password_change_requires_login(self):
        """Verify password change view requires login."""
        logger.info("Verifying login requirement for password change...")
        response = self.client.get(self.password_change_url)
        self.assertEqual(response.status_code, 302)  # Redirects to login
        expected_redirect = f"{reverse('login')}?next={self.password_change_url}"
        self.assertRedirects(response, expected_redirect, fetch_redirect_response=False)
        logger.info("Login requirement for password change verified.")

    def test_password_reset_accessible_anonymously(self):
        """Verify password reset view is accessible without login."""
        logger.info("Verifying anonymous access for password reset...")
        response = self.client.get(self.password_reset_url)
        self.assertEqual(response.status_code, 200)
        logger.info("Anonymous access for password reset verified.")

    def test_password_change_template_rendering(self):
        """Verify password change form template renders correctly."""
        logger.info("Verifying password_change_form.html rendering...")
        self.client.login(username="pwdtester", password="password123")
        response = self.client.get(self.password_change_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_change_form.html")
        self.assertTemplateUsed(response, "pages/base.html")  # Check base is extended
        self.assertIsInstance(response.context["form"], PasswordChangeForm)
        self.assertContains(response, "csrfmiddlewaretoken")  # Check CSRF token
        logger.info("password_change_form.html rendering verified.")

    def test_password_change_done_template_rendering(self):
        """Verify password change done template renders correctly."""
        logger.info("Verifying password_change_done.html rendering...")
        self.client.login(username="pwdtester", password="password123")
        response = self.client.get(self.password_change_done_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_change_done.html")
        self.assertTemplateUsed(response, "pages/base.html")
        logger.info("password_change_done.html rendering verified.")

    def test_password_reset_template_rendering(self):
        """Verify password reset form template renders correctly."""
        logger.info("Verifying password_reset_form.html rendering...")
        response = self.client.get(self.password_reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_form.html")
        self.assertTemplateUsed(response, "pages/base.html")
        self.assertIsInstance(response.context["form"], PasswordResetForm)
        self.assertContains(response, "csrfmiddlewaretoken")
        logger.info("password_reset_form.html rendering verified.")

    def test_password_reset_done_template_rendering(self):
        """Verify password reset done template renders correctly."""
        logger.info("Verifying password_reset_done.html rendering...")
        response = self.client.get(self.password_reset_done_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_done.html")
        self.assertTemplateUsed(response, "pages/base.html")
        logger.info("password_reset_done.html rendering verified.")

    # Note: Testing password_reset_confirm requires generating a valid token,
    # which is beyond simple template rendering checks. We rely on manual E2E
    # and Django's own tests for that view's core logic.
    # We can still test basic template rendering for the *complete* page though.

    def test_password_reset_complete_template_rendering(self):
        """Verify password reset complete template renders correctly."""
        logger.info("Verifying password_reset_complete.html rendering...")
        response = self.client.get(self.password_reset_complete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/password_reset_complete.html")
        self.assertTemplateUsed(response, "pages/base.html")
        logger.info("password_reset_complete.html rendering verified.")
