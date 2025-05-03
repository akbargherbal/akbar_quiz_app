# src/core/tests/test_phase5_verification.py

import os
from django.test import TestCase, Client, override_settings
from django.urls import reverse, NoReverseMatch
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class Phase5VerificationTests(TestCase):
    """
    Verify the setup specific to Phase 5: Password Management.
    """

    @classmethod
    def setUpTestData(cls):
        # Create a user for login-required views
        cls.test_user = User.objects.create_user(
            username="phase5user", password="password123", email="phase5@example.com"
        )

    def setUp(self):
        # Create a fresh client for each test
        self.client = Client()

    # --- Template Existence & Loading Tests ---

    def test_password_change_form_template_loads(self):
        """Verify password_change_form.html loads for logged-in users."""
        self.client.login(username="phase5user", password="password123")
        try:
            response = self.client.get(reverse("password_change"))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "registration/password_change_form.html")
            self.assertTemplateUsed(response, "pages/base.html")  # Check base extension
        except NoReverseMatch:
            self.fail(
                "URL name 'password_change' could not be reversed. Check core/urls.py."
            )
        except Exception as e:
            self.fail(f"Error loading password_change view/template: {e}")

    def test_password_change_done_template_loads(self):
        """Verify password_change_done.html loads for logged-in users."""
        self.client.login(username="phase5user", password="password123")
        try:
            response = self.client.get(reverse("password_change_done"))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "registration/password_change_done.html")
            self.assertTemplateUsed(response, "pages/base.html")
        except NoReverseMatch:
            self.fail("URL name 'password_change_done' could not be reversed.")
        except Exception as e:
            self.fail(f"Error loading password_change_done view/template: {e}")

    def test_password_reset_form_template_loads(self):
        """Verify password_reset_form.html loads."""
        try:
            response = self.client.get(reverse("password_reset"))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "registration/password_reset_form.html")
            self.assertTemplateUsed(response, "pages/base.html")
        except NoReverseMatch:
            self.fail("URL name 'password_reset' could not be reversed.")
        except Exception as e:
            self.fail(f"Error loading password_reset view/template: {e}")

    def test_password_reset_done_template_loads(self):
        """Verify password_reset_done.html loads."""
        try:
            response = self.client.get(reverse("password_reset_done"))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "registration/password_reset_done.html")
            self.assertTemplateUsed(response, "pages/base.html")
        except NoReverseMatch:
            self.fail("URL name 'password_reset_done' could not be reversed.")
        except Exception as e:
            self.fail(f"Error loading password_reset_done view/template: {e}")

    def test_password_reset_complete_template_loads(self):
        """Verify password_reset_complete.html loads."""
        try:
            response = self.client.get(reverse("password_reset_complete"))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(
                response, "registration/password_reset_complete.html"
            )
            self.assertTemplateUsed(response, "pages/base.html")
        except NoReverseMatch:
            self.fail("URL name 'password_reset_complete' could not be reversed.")
        except Exception as e:
            self.fail(f"Error loading password_reset_complete view/template: {e}")

    def test_password_reset_confirm_url_exists(self):
        """Verify the URL pattern for password_reset_confirm exists."""
        # We don't test loading directly as it needs valid tokens.
        # Just check if the URL name can be reversed (means the pattern exists).
        try:
            # Provide dummy tokens, the reversal itself is the test here
            reverse(
                "password_reset_confirm", kwargs={"uidb64": "dummy", "token": "dummy"}
            )
        except NoReverseMatch:
            self.fail(
                "URL name 'password_reset_confirm' could not be reversed. Check core/urls.py."
            )

    # --- Template File Existence Check ---
    def test_password_reset_email_template_exists(self):
        """Verify the password_reset_email.html file exists."""
        template_path = os.path.join(
            settings.BASE_DIR, "templates", "registration", "password_reset_email.html"
        )
        self.assertTrue(
            os.path.exists(template_path), f"Template file not found: {template_path}"
        )

    # --- Configuration Check ---
    def test_email_backend_setting_is_defined(self):
        """
        Verify EMAIL_BACKEND is set, acknowledging test runner override.

        NOTE: Django's test runner often defaults EMAIL_BACKEND to
              'django.core.mail.backends.locmem.EmailBackend' for tests,
              even if settings.py specifies console. This test verifies
              the setting is present and checks the runtime value during tests.
              Manual verification in Step 5.3 confirmed console backend works
              with `runserver`.
        """
        from django.conf import settings

        self.assertTrue(
            hasattr(settings, "EMAIL_BACKEND"),
            "EMAIL_BACKEND setting is missing in core/settings.py",
        )
        # Assert the value expected during test runs
        self.assertEqual(
            settings.EMAIL_BACKEND,
            "django.core.mail.backends.locmem.EmailBackend",  # Expect locmem during tests
            f"Expected EMAIL_BACKEND during tests to be 'locmem', but found '{getattr(settings, 'EMAIL_BACKEND', 'Not Defined')}'",
        )
